"""
MCP Client Tools for PRD Storage and Retrieval
Provides ADK tools that communicate with the MCP server
"""

import os
import json
from typing import Dict, Optional
from google.adk.tools.tool_context import ToolContext
import google.auth
from google.auth.transport.requests import Request as AuthRequest
import requests


class MCPPRDTool:
    """Client for communicating with PRD MCP server"""

    def __init__(self, mcp_server_url: str):
        self.mcp_server_url = mcp_server_url
        self.credentials, self.project = google.auth.default()

    def _get_id_token(self) -> str:
        """Get OIDC ID token for Cloud Run authentication"""
        # Refresh credentials to get ID token
        auth_req = AuthRequest()
        self.credentials.refresh(auth_req)

        # Get ID token for the target audience (MCP server URL)
        if hasattr(self.credentials, 'id_token'):
            return self.credentials.id_token

        # If using service account, get ID token for target audience
        from google.oauth2 import service_account
        from google.auth import compute_engine

        if isinstance(self.credentials, (service_account.Credentials, compute_engine.Credentials)):
            # Create ID token request
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            target_audience = self.mcp_server_url
            request = google_requests.Request()

            token = id_token.fetch_id_token(request, target_audience)
            return token

        raise ValueError("Unable to obtain ID token for authentication")

    def _call_mcp_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        Generic MCP tool caller with authentication.
        Calls the MCP server's SSE endpoint.
        """
        try:
            # Get ID token for authentication
            id_token = self._get_id_token()

            # Prepare request
            headers = {
                "Authorization": f"Bearer {id_token}",
                "Content-Type": "application/json"
            }

            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }

            # Call MCP server
            response = requests.post(
                f"{self.mcp_server_url}/sse",
                headers=headers,
                json=payload,
                timeout=60
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse SSE response
            # SSE format: "data: {json}\n\n"
            response_text = response.text.strip()
            if response_text.startswith("data: "):
                json_data = response_text[6:]  # Remove "data: " prefix
                return json.loads(json_data)

            return json.loads(response_text)

        except requests.exceptions.RequestException as e:
            return {
                "error": f"MCP server request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "error": f"Unexpected error calling MCP tool: {str(e)}"
            }

    def search_existing_prds(self, query: str) -> str:
        """
        Search for existing PRDs by query.
        Returns JSON string with search results.
        """
        result = self._call_mcp_tool("search_existing_prds", {"query": query})

        if "error" in result:
            return json.dumps({"error": result["error"], "results": []})

        # Extract content from MCP response
        if "content" in result and len(result["content"]) > 0:
            content_text = result["content"][0].get("text", "{}")
            return content_text

        return json.dumps(result)

    def get_prd(self, prd_id: str) -> str:
        """
        Retrieve a specific PRD by ID.
        Returns JSON string with PRD content and metadata.
        """
        result = self._call_mcp_tool("get_prd", {"prd_id": prd_id})

        if "error" in result:
            return json.dumps({"error": result["error"]})

        # Extract content from MCP response
        if "content" in result and len(result["content"]) > 0:
            content_text = result["content"][0].get("text", "{}")
            return content_text

        return json.dumps(result)

    def store_prd_with_confirmation(
        self,
        product_name: str,
        content: str,
        tool_context: ToolContext,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Store a PRD with human-in-the-loop confirmation.
        Requires user approval before saving to MCP server.
        """
        # Check if this is the confirmation response
        tool_confirmation = tool_context.tool_confirmation

        if not tool_confirmation:
            # First call - request user confirmation
            # Show PRD preview to user
            preview_length = min(500, len(content))
            preview = content[:preview_length]
            if len(content) > preview_length:
                preview += "\n\n... (truncated)"

            tool_context.request_confirmation(
                hint=f"""Please review the PRD for '{product_name}' and approve saving it to storage.

PRD Preview:
{preview}

This will save the PRD to Cloud Storage and make it searchable for future use."""
            )
            return "Awaiting user confirmation to store PRD"

        # User confirmed - proceed with storage
        result = self._call_mcp_tool("store_prd", {
            "product_name": product_name,
            "content": content,
            "metadata": metadata or {}
        })

        if "error" in result:
            return json.dumps({"error": result["error"], "success": False})

        # Extract content from MCP response
        if "content" in result and len(result["content"]) > 0:
            content_text = result["content"][0].get("text", "{}")
            return content_text

        return json.dumps(result)


# Initialize MCP client
mcp_server_url = os.getenv("MCP_SERVER_URL")

if not mcp_server_url:
    # Provide helpful error message if URL not configured
    print("WARNING: MCP_SERVER_URL not set in environment. MCP tools will not work.")
    print("Please set MCP_SERVER_URL in your .env file after deploying the MCP server.")
    mcp_tool = None
else:
    mcp_tool = MCPPRDTool(mcp_server_url)


# Export functions directly as tools (ADK uses plain functions, not Tool objects)
def search_existing_prds(query: str) -> str:
    """
    Search for existing PRDs to avoid duplicate work.
    Returns list of matching PRDs with summaries and relevance scores.

    Args:
        query: Search query to find similar PRDs

    Returns:
        JSON string with search results
    """
    if not mcp_tool:
        return json.dumps({
            "error": "MCP_SERVER_URL not configured. Please deploy MCP server and set MCP_SERVER_URL in .env",
            "results": []
        })
    return mcp_tool.search_existing_prds(query)


def get_prd(prd_id: str) -> str:
    """
    Retrieve the full content of a specific PRD by its ID.
    Use this after finding PRDs with search_existing_prds.

    Args:
        prd_id: The unique identifier of the PRD to retrieve

    Returns:
        JSON string with PRD content and metadata
    """
    if not mcp_tool:
        return json.dumps({
            "error": "MCP_SERVER_URL not configured. Please deploy MCP server and set MCP_SERVER_URL in .env"
        })
    return mcp_tool.get_prd(prd_id)


def store_prd(
    product_name: str,
    content: str,
    author: str = "PM Agent",
    version: str = "1.0"
) -> str:
    """
    Store a new PRD to Cloud Storage directly (no confirmation).
    The PRD will be searchable for future use.

    Note: User confirmation should be handled conversationally before calling this tool.

    Args:
        product_name: Name of the product
        content: Full PRD content in markdown format
        author: Author of the PRD (default: "PM Agent")
        version: Version of the PRD (default: "1.0")

    Returns:
        JSON string with storage result
    """
    if not mcp_tool:
        return json.dumps({
            "error": "MCP_SERVER_URL not configured. Please deploy MCP server and set MCP_SERVER_URL in .env",
            "success": False
        })

    # Build metadata from simple parameters
    metadata = {
        "author": author,
        "version": version
    }

    # Call MCP server directly without confirmation
    result = mcp_tool._call_mcp_tool("store_prd", {
        "product_name": product_name,
        "content": content,
        "metadata": metadata
    })

    if "error" in result:
        return json.dumps({"error": result["error"], "success": False})

    # Extract content from MCP response
    if "content" in result and len(result["content"]) > 0:
        content_text = result["content"][0].get("text", "{}")
        return content_text

    return json.dumps(result)


__all__ = ["search_existing_prds", "get_prd", "store_prd"]
