"""
MCP Server for PRD Storage and Retrieval
Implements Model Context Protocol over Server-Sent Events (SSE)
"""

import os
import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse
from storage import PRDStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="PRD MCP Server", version="1.0.0")

# Initialize PRD storage
BUCKET_NAME = os.getenv("BUCKET_NAME", "your-prd-storage")
DATASTORE_ID = os.getenv("DATASTORE_ID", "your-datastore-id")
PROJECT_ID = os.getenv("PROJECT_ID", "your-project-id")

storage = PRDStorage(
    bucket_name=BUCKET_NAME,
    datastore_id=DATASTORE_ID,
    project_id=PROJECT_ID
)


# MCP Protocol Handlers
def handle_list_tools() -> Dict[str, Any]:
    """Return list of available MCP tools"""
    return {
        "tools": [
            {
                "name": "search_existing_prds",
                "description": "Search for existing PRDs using full-text semantic search. Returns list of matching PRDs with summaries.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query to find similar PRDs"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_prd",
                "description": "Retrieve the full content of a specific PRD by its ID.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "prd_id": {
                            "type": "string",
                            "description": "The unique identifier of the PRD to retrieve"
                        }
                    },
                    "required": ["prd_id"]
                }
            },
            {
                "name": "store_prd",
                "description": "Store a new PRD to Cloud Storage. Requires user confirmation before saving.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "product_name": {
                            "type": "string",
                            "description": "Name of the product"
                        },
                        "content": {
                            "type": "string",
                            "description": "Full PRD content in markdown format"
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional metadata for the PRD"
                        }
                    },
                    "required": ["product_name", "content"]
                }
            }
        ]
    }


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool call and return the result"""
    try:
        if tool_name == "search_existing_prds":
            query = arguments.get("query", "")
            if not query:
                return {
                    "error": "Missing required argument: query"
                }

            results = storage.search_prds(query)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "query": query,
                            "results_count": len(results),
                            "results": results
                        }, indent=2)
                    }
                ]
            }

        elif tool_name == "get_prd":
            prd_id = arguments.get("prd_id", "")
            if not prd_id:
                return {
                    "error": "Missing required argument: prd_id"
                }

            prd = storage.get_prd(prd_id)
            if not prd:
                return {
                    "error": f"PRD not found: {prd_id}"
                }

            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(prd, indent=2)
                    }
                ]
            }

        elif tool_name == "store_prd":
            product_name = arguments.get("product_name", "")
            content = arguments.get("content", "")
            metadata = arguments.get("metadata", {})

            if not product_name or not content:
                return {
                    "error": "Missing required arguments: product_name and content"
                }

            result = storage.store_prd(product_name, content, metadata)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }

        else:
            return {
                "error": f"Unknown tool: {tool_name}"
            }

    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return {
            "error": f"Tool execution failed: {str(e)}"
        }


# MCP SSE Endpoint
async def mcp_sse_generator(request_data: Dict[str, Any]):
    """Generate Server-Sent Events for MCP protocol"""
    method = request_data.get("method", "")
    params = request_data.get("params", {})

    try:
        if method == "tools/list":
            response = handle_list_tools()
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            response = handle_tool_call(tool_name, arguments)
        else:
            response = {"error": f"Unknown method: {method}"}

        # Format as SSE
        yield f"data: {json.dumps(response)}\n\n"

    except Exception as e:
        logger.error(f"Error processing MCP request: {str(e)}")
        error_response = {"error": str(e)}
        yield f"data: {json.dumps(error_response)}\n\n"


@app.post("/sse")
async def mcp_endpoint(request: Request):
    """
    Main MCP endpoint using Server-Sent Events.
    Handles both tools/list and tools/call methods.
    """
    try:
        request_data = await request.json()
        logger.info(f"Received MCP request: {request_data.get('method')}")

        return StreamingResponse(
            mcp_sse_generator(request_data),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        logger.error(f"Error in MCP endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "prd-mcp-server",
        "bucket": BUCKET_NAME,
        "datastore": DATASTORE_ID,
        "project": PROJECT_ID
    }


@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "PRD MCP Server",
        "version": "1.0.0",
        "description": "Model Context Protocol server for PRD storage and retrieval",
        "endpoints": {
            "/sse": "MCP protocol endpoint (POST)",
            "/health": "Health check (GET)",
            "/": "API information (GET)"
        },
        "tools": [
            "search_existing_prds",
            "get_prd",
            "store_prd"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
