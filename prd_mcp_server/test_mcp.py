#!/usr/bin/env python3
"""
Test script for MCP server functionality
"""

import json
import requests
import google.auth
from google.auth.transport.requests import Request as AuthRequest
from google.oauth2 import id_token

MCP_SERVER_URL = "https://prd-mcp-server-4bz26qs7xq-uc.a.run.app"


def get_id_token():
    """Get ID token for Cloud Run authentication"""
    auth_req = AuthRequest()
    token = id_token.fetch_id_token(auth_req, MCP_SERVER_URL)
    return token


def test_health():
    """Test MCP server health endpoint"""
    print("Testing health endpoint...")
    token = get_id_token()
    response = requests.get(
        f"{MCP_SERVER_URL}/health",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")


def test_list_tools():
    """Test MCP tools/list method"""
    print("Testing tools/list...")
    token = get_id_token()
    response = requests.post(
        f"{MCP_SERVER_URL}/sse",
        headers={"Authorization": f"Bearer {token}"},
        json={"method": "tools/list"}
    )
    print(f"Status: {response.status_code}")
    # Parse SSE response
    response_text = response.text.strip()
    if response_text.startswith("data: "):
        json_data = response_text[6:]
        print(f"Response: {json.dumps(json.loads(json_data), indent=2)}\n")
    else:
        print(f"Raw response: {response_text}\n")


def test_search(query="mobile app"):
    """Test search_existing_prds tool"""
    print(f"Testing search_existing_prds with query: '{query}'...")
    token = get_id_token()
    response = requests.post(
        f"{MCP_SERVER_URL}/sse",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "method": "tools/call",
            "params": {
                "name": "search_existing_prds",
                "arguments": {"query": query}
            }
        }
    )
    print(f"Status: {response.status_code}")
    response_text = response.text.strip()
    if response_text.startswith("data: "):
        json_data = response_text[6:]
        result = json.loads(json_data)
        if "content" in result and len(result["content"]) > 0:
            content = json.loads(result["content"][0]["text"])
            print(f"Search Results: {json.dumps(content, indent=2)}\n")
        else:
            print(f"Response: {json.dumps(result, indent=2)}\n")
    else:
        print(f"Raw response: {response_text}\n")


def test_store_prd():
    """Test store_prd tool"""
    print("Testing store_prd...")

    sample_prd = """# Test Product

## Problem Statement
This is a test PRD to verify the storage functionality of the MCP server.

## User Stories
- As a user, I want to test PRD storage
- As a developer, I want to verify the MCP integration

## Key Functional Requirements
- Store PRDs in GCS
- Enable search via Vertex AI Search
- Support HITL confirmation
"""

    token = get_id_token()
    response = requests.post(
        f"{MCP_SERVER_URL}/sse",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "method": "tools/call",
            "params": {
                "name": "store_prd",
                "arguments": {
                    "product_name": "Test Product",
                    "content": sample_prd,
                    "metadata": {
                        "author": "MCP Test Script",
                        "version": "1.0"
                    }
                }
            }
        }
    )
    print(f"Status: {response.status_code}")
    response_text = response.text.strip()
    if response_text.startswith("data: "):
        json_data = response_text[6:]
        result = json.loads(json_data)
        if "content" in result and len(result["content"]) > 0:
            content = json.loads(result["content"][0]["text"])
            print(f"Store Result: {json.dumps(content, indent=2)}\n")
        else:
            print(f"Response: {json.dumps(result, indent=2)}\n")
    else:
        print(f"Raw response: {response_text}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)
    print()

    try:
        test_health()
        test_list_tools()
        test_search("test")
        test_store_prd()

        # Search again to verify storage
        print("Searching for the stored PRD...")
        test_search("test product")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
