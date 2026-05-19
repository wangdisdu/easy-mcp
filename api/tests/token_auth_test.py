"""
Tests for MCP token authentication and per-token tool scoping.

Uses an in-memory SQLite database so the full service/query path is exercised.
"""

import unittest

from fastapi import HTTPException
from starlette.requests import Request

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

# Import model modules so all tables are registered on SQLModel.metadata.
from api.models import tb_user, tb_tool, tb_func, tb_config, tb_tag, tb_token  # noqa: F401
from api.models.tb_tool import TbTool
from api.schemas.token_schema import TokenCreate, TokenUpdate
from api.services.mcp_service import MCPService
from api.services.token_service import TokenService
from api.services.tool_service import ToolService
from api.utils.mcp_auth import verify_mcp_token
from api.utils.time_util import get_current_unix_ms


def _request(authorization: str = None) -> Request:
    """Build a minimal Starlette Request, optionally with a bearer header."""
    headers = []
    if authorization is not None:
        headers.append((b"authorization", authorization.encode()))
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/mcp",
            "query_string": b"",
            "headers": headers,
        }
    )


async def _make_tool(db: AsyncSession, name: str, code: str = "result = {'ok': True}"):
    """Insert a minimal enabled basic tool and return it."""
    now = get_current_unix_ms()
    tool = TbTool(
        name=name,
        description=name,
        type="basic",
        setting="{}",
        parameters="{}",
        code=code,
        is_enabled=True,
        created_at=now,
        updated_at=now,
        created_by="tester",
        updated_by="tester",
    )
    db.add(tool)
    await db.commit()
    await db.refresh(tool)
    return tool


class TokenAuthTest(unittest.IsolatedAsyncioTestCase):
    """Token CRUD, lookup and tool-scoping behavior."""

    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite://", future=True)
        async with self.engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        self.session_factory = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def asyncTearDown(self):
        await self.engine.dispose()

    async def test_create_token_generates_prefixed_secret(self):
        async with self.session_factory() as db:
            svc = TokenService(db)
            token, tool_ids = await svc.create_token(
                TokenCreate(name="t1", tool_ids=[]), "admin"
            )
            self.assertTrue(token.token.startswith("emcp_"))
            self.assertEqual(tool_ids, [])

    async def test_get_token_by_value(self):
        async with self.session_factory() as db:
            svc = TokenService(db)
            token, _ = await svc.create_token(
                TokenCreate(name="t1", tool_ids=[]), "admin"
            )
            secret = token.token

            found = await svc.get_token_by_value(secret)
            self.assertIsNotNone(found)

            self.assertIsNone(await svc.get_token_by_value("emcp_nope"))
            self.assertIsNone(await svc.get_token_by_value(""))

    async def test_tool_scope_binding_and_update(self):
        async with self.session_factory() as db:
            tool_a = await _make_tool(db, "a")
            tool_b = await _make_tool(db, "b")
            svc = TokenService(db)

            token, ids = await svc.create_token(
                TokenCreate(name="t1", tool_ids=[tool_a.id]), "admin"
            )
            self.assertEqual(ids, [tool_a.id])
            self.assertEqual(await svc.get_tool_ids_for_token(token.id), [tool_a.id])

            # Replace bindings via update.
            _, ids2 = await svc.update_token(
                token.id, TokenUpdate(tool_ids=[tool_b.id]), "admin"
            )
            self.assertEqual(ids2, [tool_b.id])

    async def test_query_tools_tool_ids_filter(self):
        async with self.session_factory() as db:
            await _make_tool(db, "a")
            tool_b = await _make_tool(db, "b")
            svc = ToolService(db)

            # None => no restriction
            tools, total = await svc.query_tools(tool_ids=None)
            self.assertEqual(total, 2)

            # Empty list => no tools (least privilege)
            tools, total = await svc.query_tools(tool_ids=[])
            self.assertEqual(total, 0)
            self.assertEqual(tools, [])

            # Subset
            tools, total = await svc.query_tools(tool_ids=[tool_b.id])
            self.assertEqual(total, 1)
            self.assertEqual(tools[0].id, tool_b.id)

    async def test_mcp_list_tools_scoped_by_token(self):
        async with self.session_factory() as db:
            tool_a = await _make_tool(db, "a")
            await _make_tool(db, "b")
            mcp = MCPService(db)

            # No scope -> all enabled tools
            self.assertEqual(len(await mcp.list_tools(None, None)), 2)

            # Scoped to tool_a only
            scoped = await mcp.list_tools(None, [tool_a.id])
            self.assertEqual([t.name for t in scoped], ["a"])

            # Empty scope -> nothing
            self.assertEqual(await mcp.list_tools(None, []), [])

    async def test_mcp_call_tool_denied_when_out_of_scope(self):
        async with self.session_factory() as db:
            tool_a = await _make_tool(db, "a")
            tool_b = await _make_tool(db, "b")
            mcp = MCPService(db)

            # tool_b not in scope -> denied without execution
            result = await mcp.call_tool("b", {}, [tool_a.id])
            self.assertEqual(len(result), 1)
            self.assertIn("not authorized", result[0].text)

            # tool_a in scope -> executes and returns result
            ok = await mcp.call_tool("a", {}, [tool_a.id])
            self.assertIn("ok", ok[0].text)
            # unknown name still handled
            missing = await mcp.call_tool("nope", {}, [tool_a.id, tool_b.id])
            self.assertIn("not found", missing[0].text)

    async def test_auth_fail_open_when_no_tokens(self):
        async with self.session_factory() as db:
            # No tokens configured -> open mode, no restriction.
            scope = await verify_mcp_token(_request(), db)
            self.assertIsNone(scope.allowed_tool_ids)
            self.assertEqual(scope.token_id, 0)

    async def test_auth_enforced_once_a_token_exists(self):
        async with self.session_factory() as db:
            tool_a = await _make_tool(db, "a")
            svc = TokenService(db)
            token, _ = await svc.create_token(
                TokenCreate(name="t1", tool_ids=[tool_a.id]), "admin"
            )

            # Missing token -> 401
            with self.assertRaises(HTTPException) as ctx:
                await verify_mcp_token(_request(), db)
            self.assertEqual(ctx.exception.status_code, 401)

            # Wrong token -> 401
            with self.assertRaises(HTTPException):
                await verify_mcp_token(_request("Bearer emcp_wrong"), db)

            # Valid token -> scoped to its tools
            scope = await verify_mcp_token(_request(f"Bearer {token.token}"), db)
            self.assertEqual(scope.allowed_tool_ids, [tool_a.id])
            self.assertEqual(scope.token_id, token.id)

    async def test_delete_token_revokes_and_reopens_when_empty(self):
        async with self.session_factory() as db:
            svc = TokenService(db)
            token, _ = await svc.create_token(
                TokenCreate(name="t1", tool_ids=[]), "admin"
            )
            secret = token.token

            # While the token exists, auth is enforced.
            with self.assertRaises(HTTPException):
                await verify_mcp_token(_request(), db)

            # Deleting the only token revokes it and reopens MCP (fail-open).
            await svc.delete_token(token.id, "admin")
            self.assertIsNone(await svc.get_token_by_value(secret))
            scope = await verify_mcp_token(_request(), db)
            self.assertIsNone(scope.allowed_tool_ids)


if __name__ == "__main__":
    unittest.main()
