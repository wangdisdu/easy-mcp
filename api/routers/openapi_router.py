"""
OpenAPI router.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models.tb_user import TbUser
from api.schemas.common_schema import Response
from api.schemas.openapi_schema import OpenApi
from api.schemas.tool_schema import ToolResponse
from api.services.openapi_service import OpenApiService
from api.utils.security_util import get_current_user

# Get logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/tool-openapi", tags=["tool-openapi"])


@router.post("/analyze", response_model=Response[OpenApi])
async def analyze_openapi(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Analyze OpenAPI file.

    Args:
        file: OpenAPI file
        db: Database session
        current_user: Current user

    Returns:
        Response[OpenApiAnalysisResponse]: Analysis result
    """
    # Read file content
    file_content = await file.read()

    # Analyze OpenAPI file
    service = OpenApiService(db)
    result = await service.analyze_openapi(file_content)

    return Response(data=result)


@router.post("/import", response_model=Response[List[ToolResponse]])
async def import_openapi(
    import_data: OpenApi,
    db: AsyncSession = Depends(get_db),
    current_user: TbUser = Depends(get_current_user),
):
    """
    Import OpenAPI tools.

    Args:
        import_data: Import data
        db: Database session
        current_user: Current user

    Returns:
        Response[List[ToolResponse]]: Imported tools
    """
    # Import OpenAPI tools
    service = OpenApiService(db)
    tools = await service.import_openapi_tools(
        server=import_data.server,
        apis=import_data.apis,
        current_user=current_user.username,
    )

    # Convert to response
    tool_responses = [ToolResponse.model_validate(tool) for tool in tools]

    return Response(data=tool_responses)
