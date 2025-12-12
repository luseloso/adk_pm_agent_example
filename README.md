# ADK PM Agent Example

An AI-powered Product Management Agent that creates comprehensive Product Requirements Documents (PRDs) through a sequential multi-agent workflow with human oversight.

## Overview

This example demonstrates how to build a production-ready AI agent system using Google's Agent Development Kit (ADK). The agent takes a product idea and generates a complete PRD by:

1. **Researching the market** - Uses Google Search to understand the problem space, competitors, and target audience
2. **Mapping user journeys** - Creates detailed personas and user journeys based on research
3. **Writing the PRD** - Compiles everything into a structured Product Requirements Document
4. **Storing for reuse** - Saves PRDs in both markdown (editable) and HTML (shareable) formats with semantic search

**Key Features:**
- **Human-in-the-Loop**: Two confirmation points (duplicate check + final approval) give users control
- **Sequential Workflow**: Each agent builds on the previous agent's output for consistent, high-quality results
- **Cloud Storage**: PRDs stored in Google Cloud Storage with Vertex AI Search integration
- **MCP Protocol**: Custom Model Context Protocol server for standardized tool integration

## What You'll Learn

- Building multi-agent systems with sequential workflows
- Implementing human-in-the-loop patterns for agent oversight
- Creating custom MCP servers for tool integration
- Deploying agents to Vertex AI Agent Engine
- Integrating with Google Cloud services (Storage, Search, Cloud Run)

## Architecture

### High-Level Flow

```
User: "Create a PRD for a fitness tracking app"
  │
  ▼
┌─────────────────────────────────────────┐
│ root_agent (Orchestrator)              │
│                                         │
│ 1. Check for duplicate PRDs             │ ← HITL #1: User decides
│    (via MCP server search)              │   if duplicate exists
│                                         │
│ 2. Delegate to Sequential Workflow     │
└────────────┬────────────────────────────┘
             │
             ▼
┌────────────────────────────────────────────────────┐
│ virtual_product_manager_agent (Sequential)        │
│                                                    │
│  ┌──────────────────┐                            │
│  │ Market Researcher │ → Google Search            │
│  │   (gemini-flash)  │    for market research     │
│  └─────────┬─────────┘                            │
│            │                                       │
│            ▼                                       │
│  ┌──────────────────┐                            │
│  │  User Journey    │ → Create personas          │
│  │   (gemini-pro)   │    and user journeys       │
│  └─────────┬─────────┘                            │
│            │                                       │
│            ▼                                       │
│  ┌──────────────────┐                            │
│  │  PRD Scripter    │ → Compile complete PRD     │
│  │   (gemini-pro)   │    Save to /tmp file       │
│  └─────────┬─────────┘                            │
└────────────┼────────────────────────────────────┘
             │
             ▼
    Present PRD to user                   ← HITL #2: User approves
             │                               before saving
             ▼
┌─────────────────────────────────────────┐
│ MCP Server (Cloud Run)                  │
│                                         │
│ Store PRD in dual format:              │
│ • prds/product_123.md  (editable)      │
│ • prds/product_123.html (shareable)    │
│                                         │
│ Index in Vertex AI Search              │
└─────────────────────────────────────────┘
             │
             ▼
    Return shareable HTML URL
```

### Components

**1. PM Agent** (`pm_agent/`)
- Built with Google ADK
- Deployed to Vertex AI Agent Engine
- Sequential workflow with 3 specialized sub-agents
- Tools: Google Search, MCP server (search/store PRDs)

**2. MCP Server** (`prd_mcp_server/`)
- FastAPI server implementing Model Context Protocol
- Deployed to Cloud Run
- Stores PRDs in Google Cloud Storage
- Integrates with Vertex AI Search for semantic search

### Human-in-the-Loop Pattern

Two confirmation points ensure user control:

**HITL #1: Duplicate Prevention**
```
User: "Create a PRD for a task management app"
Agent: "I found 2 similar PRDs. Would you like to:"
       "a) View existing PRD: project_mgmt_app_456"
       "b) Create new PRD anyway"
       "c) Refine your idea"
User: [makes choice]
```

**HITL #2: PRD Approval**
```
Agent: [Presents complete PRD]
       "Would you like me to save this PRD to storage?"
User: "yes" → Saves to cloud
User: "refine the user stories" → Makes changes
```

### Data Flow

```
Product Idea
    ↓
Duplicate Check (MCP search)
    ↓
Market Research (Google Search)
    ↓
User Journeys & Personas
    ↓
PRD Generation → /tmp/temp_prd_draft.md
    ↓
User Approval (HITL)
    ↓
MCP Server Storage
    ├→ GCS: prds/product.md (markdown)
    ├→ GCS: prds/product.html (HTML)
    └→ Vertex AI Search: Index HTML
    ↓
Return shareable URL
```

## Project Structure

```
adk_pm_agent_example/
├── pm_agent/                    # AI Agent (Google ADK)
│   ├── agent.py                 # Agent definitions & workflow
│   ├── mcp_tool.py              # MCP server integration
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── prd_mcp_server/              # MCP Server (FastAPI)
│   ├── server.py                # MCP protocol handlers
│   ├── storage.py               # GCS & Vertex AI Search
│   ├── deploy.sh                # Cloud Run deployment
│   ├── configure_security.sh    # IAM configuration
│   ├── Dockerfile
│   └── README.md
│
├── docs/                        # Documentation
│   ├── ARCHITECTURE.md          # Detailed architecture
│   ├── DEPLOYMENT.md            # Deployment guide
│   └── LOCAL_TESTING.md         # Testing guide
│
├── examples/                    # Usage examples
│   ├── local_test/
│   ├── custom_product/
│   └── deploy_and_test/
│
└── README.md                    # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- Google Cloud Project with billing enabled
- Google Cloud SDK (`gcloud`)
- Google ADK: `pip install google-cloud-aiplatform[adk,agent_engines]`

**Required GCP APIs:**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable discoveryengine.googleapis.com
```

### Deployment

**Step 1: Deploy MCP Server**

The MCP server must be deployed first, as the PM agent needs its URL.

```bash
cd prd_mcp_server

# Configure environment
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET_NAME="your-prd-storage"
export DATASTORE_ID="your-datastore-id"

# Deploy to Cloud Run
./deploy.sh

# Configure IAM permissions
./configure_security.sh
```

Save the MCP server URL from the output (e.g., `https://prd-mcp-server-XXX.run.app`)

**Step 2: Configure PM Agent**

```bash
cd ../pm_agent

# Create environment file
cp .env.example .env

# Edit .env with your values:
# - GOOGLE_CLOUD_PROJECT=your-project-id
# - GOOGLE_CLOUD_LOCATION=us-central1
# - GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket
# - MCP_SERVER_URL=https://your-mcp-server.run.app
```

**Step 3: Deploy PM Agent**

```bash
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --description="AI PM agent with sequential workflow" \
  --trace_to_cloud \
  pm_agent
```

**Step 4: Register to Gemini Enterprise** (Optional)

1. Go to [Gemini Enterprise Console](https://console.cloud.google.com/gemini/enterprise)
2. Click "Register Agent"
3. Use the reasoning engine resource name from deployment
4. Add icon: `https://openmoji.org/data/color/svg/1F916.svg`

### Testing Locally

Before deploying, test locally:

```bash
cd pm_agent
adk web . --port 8080

# Visit http://localhost:8080
# Try: "Create a PRD for a mobile fitness tracking app"
```

## Usage Example

**Creating a PRD:**

```
User: Create a PRD for a mobile app that helps remote workers track
      their focus time and minimize distractions

Agent: Searching for existing similar PRDs...
       No duplicates found. Proceeding with research...

       [Conducts market research via Google Search]
       [Creates user personas and journeys]
       [Generates comprehensive PRD]

       Here's the complete PRD:

       # PRD: FocusFlow - Remote Work Productivity App

       ## Problem Statement
       Remote workers struggle to maintain focus...

       ## User Stories
       1. As a remote worker, I want to...

       [Full PRD displayed]

       Would you like me to save this PRD to storage?

User: yes

Agent: PRD saved successfully!
       PRD ID: focusflow_app_1234567890
       View at: https://storage.googleapis.com/.../focusflow_app_1234567890.html
```

**Searching existing PRDs:**

```
User: Search for productivity-related PRDs

Agent: Found 3 matching PRDs:
       1. focusflow_app_1234567890 - "Remote work focus tracking"
       2. taskmaster_pro_9876543210 - "AI-powered task management"
       3. pomodoro_plus_5555555555 - "Enhanced pomodoro technique app"
```

## Configuration

### PM Agent Environment Variables

```bash
# Backend selection
GOOGLE_GENAI_USE_VERTEXAI=1

# GCP Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket

# MCP Server URL (from deployment)
MCP_SERVER_URL=https://your-mcp-server.run.app
```

### MCP Server Environment Variables

Set during deployment via `deploy.sh`:

```bash
PROJECT_ID=your-project-id
BUCKET_NAME=your-prd-storage
DATASTORE_ID=your-datastore-id
```

## Development

### Making Changes

After modifying agent code:

```bash
# Test locally first
cd pm_agent
adk web . --port 8080 --reload_agents

# Deploy when ready
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --trace_to_cloud \
  pm_agent
```

### Monitoring

**View traces:**
```
https://console.cloud.google.com/traces/list?project=your-project-id
```

**Check logs:**
```bash
# Agent logs
gcloud ai reasoning-engines list --project=your-project-id

# MCP server logs
gcloud run services logs read prd-mcp-server \
  --region=us-central1 \
  --project=your-project-id
```

## Documentation

- **[Architecture Details](docs/ARCHITECTURE.md)** - Deep dive into system design
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Complete deployment instructions
- **[Local Testing Guide](docs/LOCAL_TESTING.md)** - Testing and development workflow
- **[PM Agent README](pm_agent/README.md)** - Agent-specific documentation
- **[MCP Server README](prd_mcp_server/README.md)** - MCP server documentation

## Troubleshooting

**Agent can't connect to MCP server:**
- Verify `MCP_SERVER_URL` in `pm_agent/.env`
- Check Cloud Run service is deployed: `gcloud run services list`
- Verify service account has Cloud Run Invoker role

**PRDs not appearing in search:**
- Allow 10-15 minutes for initial indexing in Vertex AI Search
- Verify data store is configured to index `gs://your-bucket/prds/*.html`
- Check HTML files exist: `gcloud storage ls gs://your-bucket/prds/`

**Deployment fails:**
- Enable all required APIs (see Prerequisites)
- Ensure Python 3.11+ is being used
- Check staging bucket exists and is accessible

## Learn More

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Sequential Agents Guide](https://google.github.io/adk-docs/agents/multi-agents/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/docs/generative-ai/agent-engine)
- [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs)

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file

## Acknowledgments

Built with:
- [Google ADK](https://github.com/google/adk) - Agent Development Kit
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai) - AI platform
- [FastAPI](https://fastapi.tiangolo.com/) - MCP server framework
- [Python Markdown](https://python-markdown.github.io/) - Markdown to HTML conversion
