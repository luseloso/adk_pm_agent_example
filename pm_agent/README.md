# PM Agent

AI-powered Product Management Agent built with Google ADK.

## Overview

This agent creates comprehensive Product Requirements Documents (PRDs) through a sequential multi-agent workflow with human-in-the-loop confirmation points.

## Quick Start

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Start ADK web server
adk web . --port 8080

# Visit http://localhost:8080
```

### Deployment

```bash
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --trace_to_cloud \
  pm_agent
```

## Architecture

### Agent Workflow

```
root_agent (orchestrator)
  ├─ search_existing_prds (MCP)    → HITL #1: Duplicate check
  │
  └─ virtual_product_manager_agent (sequential)
       ├─ market_researcher_agent   → Google Search for market research
       ├─ user_journey_agent         → Create personas & journeys
       └─ prd_scripter_agent         → Compile PRD → HITL #2: Approval
```

### Human-in-the-Loop Points

1. **Duplicate Detection**: Before starting, checks for similar existing PRDs
2. **PRD Approval**: After generation, waits for user confirmation before saving

## Files

- `agent.py` - Agent definitions and sequential workflow
- `mcp_tool.py` - MCP server integration for PRD storage
- `__init__.py` - Package initialization
- `requirements.txt` - Python dependencies
- `.env.example` - Environment template

## Configuration

Create `.env` file:

```bash
# Backend selection
GOOGLE_GENAI_USE_VERTEXAI=1

# GCP Configuration (for deployment)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket

# MCP Server (requires prd_mcp_server deployed)
MCP_SERVER_URL=https://your-mcp-server.run.app
```

## Usage

**Example Prompt**:
```
Create a PRD for a mobile fitness tracking app that helps users:
- Track daily workouts and nutrition
- Set and monitor fitness goals
- Connect with personal trainers
- Join community challenges
```

**Agent Response**:
1. Searches for existing similar PRDs
2. Conducts market research using Google Search
3. Creates user personas and journeys
4. Generates comprehensive PRD
5. Presents PRD and asks for confirmation
6. Saves to MCP server (returns shareable HTML URL)

## MCP Tools

The agent uses these MCP server tools:

- `search_existing_prds(query)` - Search for similar PRDs
- `get_prd(prd_id)` - Retrieve specific PRD
- `store_prd(name, content, metadata)` - Save PRD (markdown + HTML)

## Development

### Testing Changes Locally

```bash
# Enable auto-reload
adk web . --port 8080 --reload_agents
```

### Deploying Updates

```bash
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --trace_to_cloud \
  pm_agent
```

## Learn More

- [Architecture Documentation](../docs/ARCHITECTURE.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Local Testing Guide](../docs/LOCAL_TESTING.md)
- [Examples](../examples/)

## References

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Sequential Agents](https://google.github.io/adk-docs/agents/multi-agents/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
