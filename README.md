# ADK PM Agent Example

A complete example of building an AI-powered Product Management Agent using Google ADK (Agent Development Kit). This project demonstrates sequential multi-agent workflows, human-in-the-loop patterns, and cloud storage integration.

## What This Example Demonstrates

- **Sequential Agent Workflow**: Chain of specialized agents (market researcher → user journey mapper → PRD writer)
- **Human-in-the-Loop (HITL)**: Two confirmation points for user control
- **MCP Server Integration**: Custom Model Context Protocol server for PRD storage
- **Dual-Format Storage**: Markdown for editing, HTML for presentation
- **Vertex AI Search**: Semantic search across stored PRDs
- **Cloud Deployment**: Deploy to Agent Engine and register to Gemini Enterprise

## Project Structure

```
adk_pm_agent_example/
├── pm_agent/                    # Main PM Agent (Google ADK)
│   ├── pm_agent/
│   │   ├── agent.py            # Agent definitions and workflow
│   │   ├── mcp_tool.py         # MCP server integration
│   │   └── requirements.txt
│   ├── docs/                   # Documentation
│   ├── examples/               # Usage examples
│   ├── .env.example
│   ├── .gitignore
│   └── README.md
│
├── prd_mcp_server/             # MCP Server (FastAPI + GCS)
│   ├── server.py               # FastAPI MCP server
│   ├── storage.py              # GCS and Vertex AI Search
│   ├── deploy.sh               # Cloud Run deployment
│   ├── configure_security.sh   # IAM setup
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
│
├── .gitignore
├── LICENSE
└── README.md                   # This file
```

## Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project with enabled APIs:
  - Vertex AI
  - Cloud Storage
  - Cloud Run  
  - Discovery Engine (for search)
- Google Cloud SDK (`gcloud`)
- Google ADK: `pip install google-cloud-aiplatform[adk,agent_engines]`

### 1. Deploy the MCP Server

```bash
cd prd_mcp_server

# Configure your project
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET_NAME="your-prd-storage"
export DATASTORE_ID="your-datastore-id"

# Deploy to Cloud Run
./deploy.sh

# Configure security
./configure_security.sh
```

Save the MCP server URL from the deployment output.

### 2. Configure the PM Agent

```bash
cd pm_agent

# Copy environment templates
cp .env.example .env
cp pm_agent/.env.example pm_agent/.env

# Edit .env files with your configuration
```

Required environment variables:
- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `GOOGLE_CLOUD_LOCATION` - Region (e.g., us-central1)
- `GOOGLE_CLOUD_STAGING_BUCKET` - GCS bucket for deployment artifacts
- `MCP_SERVER_URL` - MCP server URL from step 1

### 3. Test Locally

```bash
cd pm_agent
adk web pm_agent --port 8080

# Visit http://localhost:8080
# Try: "Create a PRD for a mobile fitness tracking app"
```

### 4. Deploy to Agent Engine

```bash
cd pm_agent
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --description="AI-powered PM agent for creating comprehensive PRDs" \
  --trace_to_cloud \
  pm_agent
```

### 5. Register to Gemini Enterprise (Optional)

1. Go to [Gemini Enterprise Console](https://console.cloud.google.com/gemini/enterprise)
2. Click "Register Agent"
3. Use the reasoning engine resource name from deployment
4. Add icon: `https://openmoji.org/data/color/svg/1F916.svg`

## How It Works

### Agent Workflow

1. **Duplicate Detection** (HITL #1)
   - User provides product idea
   - Agent searches for existing similar PRDs
   - If found, asks user to view existing or create new
   
2. **PRD Generation** (Sequential Workflow)
   - **Market Researcher**: Uses Google Search to gather context
   - **User Journey Agent**: Creates personas and user journeys
   - **PRD Scripter**: Compiles comprehensive PRD
   
3. **User Approval** (HITL #2)
   - Agent presents complete PRD
   - Waits for user confirmation before saving
   
4. **Storage & Sharing**
   - Saves PRD to Cloud Storage (markdown + HTML)
   - Returns shareable URL for formatted view

### MCP Server

The MCP server handles:
- PRD storage in Google Cloud Storage
- Markdown to HTML conversion
- Integration with Vertex AI Search
- Semantic search across all PRDs

## Key Features

### Sequential Agent Pattern
```python
virtual_product_manager_agent = SequentialAgent(
    name="virtual_product_manager_agent",
    sub_agents=[
        market_researcher_agent,
        user_journey_agent,
        prd_scripter_agent,
    ],
)
```

### Human-in-the-Loop
Two confirmation points ensure user control:
- Duplicate detection with user choice
- PRD approval before saving

### Dual-Format Storage
PRDs stored in two formats:
- `.md` - Original markdown for editing
- `.html` - Formatted version for viewing and search indexing

## Usage Examples

### Creating a PRD
```
User: "Create a PRD for a mobile fitness tracking app"

Agent: [Searches for duplicates]
Agent: "No similar PRDs found. Proceeding with research..."
Agent: [Conducts market research with Google Search]
Agent: [Creates user journeys and personas]
Agent: [Presents complete PRD]
Agent: "Would you like me to save this PRD to storage?"

User: "yes"

Agent: "PRD saved! View at: https://storage.googleapis.com/..."
```

### Searching PRDs
```
User: "Search for fitness-related PRDs"

Agent: [Returns list of matching PRDs with summaries]
```

## Configuration

### Environment Variables

**PM Agent** (`.env` and `pm_agent/.env`):
```bash
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket
MCP_SERVER_URL=https://your-mcp-server.run.app
```

**MCP Server** (Cloud Run environment):
```bash
PROJECT_ID=your-project-id
BUCKET_NAME=your-prd-storage
DATASTORE_ID=your-datastore-id
```

## Development

### Running Tests

```bash
# Test MCP server
cd prd_mcp_server
python test_mcp.py

# Test agent locally
cd pm_agent
adk web pm_agent --port 8080 --reload_agents
```

### Making Changes

After updating the agent:
```bash
cd pm_agent
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --trace_to_cloud \
  pm_agent
```

## Architecture Highlights

### Why Sequential Agents?
Sequential agents ensure proper context flow - each agent builds upon the previous agent's output, creating a comprehensive PRD with consistent information.

### Why Human-in-the-Loop?
Two HITL checkpoints give users control:
1. Prevent duplicate work by checking existing PRDs
2. Review and approve before committing to storage

### Why MCP Server?
The MCP server provides:
- Centralized PRD storage
- Format conversion (markdown → HTML)
- Search capabilities via Vertex AI
- Separation of concerns (agent logic vs. storage)

## Troubleshooting

### Agent can't connect to MCP server
- Verify `MCP_SERVER_URL` in `pm_agent/.env`
- Check Cloud Run service is deployed: `gcloud run services list`
- Verify service account permissions

### Search not finding PRDs
- Check Vertex AI Search data store configuration
- Ensure connected to `gs://your-bucket/prds/*.html`
- Allow time for initial indexing

### Telemetry not showing
- Redeploy with `--trace_to_cloud` flag
- View traces in Cloud Console → Trace

## Learn More

- **PM Agent Details**: See `pm_agent/README.md`
- **MCP Server Details**: See `prd_mcp_server/README.md`
- **Google ADK Docs**: https://google.github.io/adk-docs/
- **Vertex AI Search**: https://cloud.google.com/generative-ai-app-builder

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License - see LICENSE file

## Acknowledgments

Built with:
- [Google ADK](https://github.com/google/adk)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Python Markdown](https://python-markdown.github.io/)
