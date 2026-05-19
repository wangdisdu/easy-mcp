"""
Test cases for _resolve_http_tool_headers.
"""

import unittest

from api.services.tool_service import _resolve_http_tool_headers


class ResolveHttpToolHeadersTest(unittest.TestCase):
    """Test cases for HTTP tool header variable resolution."""

    def test_static_value_passthrough(self):
        """Static header values are returned unchanged."""
        result = _resolve_http_tool_headers(
            [{"key": "Content-Type", "value": "application/json"}],
            {"authorization": "Bearer abc"},
        )
        self.assertEqual(
            result, [{"key": "Content-Type", "value": "application/json"}]
        )

    def test_double_quote_reference(self):
        """${header["xxx"]} is substituted from the request headers."""
        result = _resolve_http_tool_headers(
            [{"key": "Authorization", "value": '${header["authorization"]}'}],
            {"authorization": "Bearer abc"},
        )
        self.assertEqual(
            result, [{"key": "Authorization", "value": "Bearer abc"}]
        )

    def test_single_quote_reference(self):
        """Single-quoted reference syntax is also supported."""
        result = _resolve_http_tool_headers(
            [{"key": "X-Tenant", "value": "${header['x-tenant-id']}"}],
            {"x-tenant-id": "t-1"},
        )
        self.assertEqual(result, [{"key": "X-Tenant", "value": "t-1"}])

    def test_mixed_static_and_variable(self):
        """A value can mix static text with a reference."""
        result = _resolve_http_tool_headers(
            [{"key": "Authorization", "value": 'Bearer ${header["x-token"]}'}],
            {"x-token": "xyz"},
        )
        self.assertEqual(
            result, [{"key": "Authorization", "value": "Bearer xyz"}]
        )

    def test_missing_header_becomes_empty_string(self):
        """A reference to an absent request header resolves to empty string."""
        result = _resolve_http_tool_headers(
            [{"key": "Authorization", "value": '${header["authorization"]}'}],
            {"x-other": "v"},
        )
        self.assertEqual(result, [{"key": "Authorization", "value": ""}])

    def test_missing_header_with_no_request_headers(self):
        """References resolve to empty when there are no request headers."""
        result = _resolve_http_tool_headers(
            [{"key": "Authorization", "value": '${header["authorization"]}'}],
            None,
        )
        self.assertEqual(result, [{"key": "Authorization", "value": ""}])

    def test_lookup_is_case_insensitive(self):
        """Header name lookup ignores case on both sides."""
        result = _resolve_http_tool_headers(
            [{"key": "Authorization", "value": '${header["Authorization"]}'}],
            {"authorization": "Bearer abc"},
        )
        self.assertEqual(
            result, [{"key": "Authorization", "value": "Bearer abc"}]
        )

    def test_spaces_inside_placeholder(self):
        """Whitespace inside the placeholder is tolerated."""
        result = _resolve_http_tool_headers(
            [{"key": "X-A", "value": '${ header [ "x-a" ] }'}],
            {"x-a": "1"},
        )
        self.assertEqual(result, [{"key": "X-A", "value": "1"}])

    def test_legacy_dict_setting_headers(self):
        """Legacy dict-form setting headers are still supported."""
        result = _resolve_http_tool_headers(
            {"Authorization": '${header["x-token"]}', "Accept": "*/*"},
            {"x-token": "tok"},
        )
        self.assertEqual(
            result,
            [
                {"key": "Authorization", "value": "tok"},
                {"key": "Accept", "value": "*/*"},
            ],
        )

    def test_empty_setting_headers(self):
        """Empty / unsupported setting headers yield an empty list."""
        self.assertEqual(_resolve_http_tool_headers(None, {"a": "b"}), [])
        self.assertEqual(_resolve_http_tool_headers([], {"a": "b"}), [])


if __name__ == "__main__":
    unittest.main()
