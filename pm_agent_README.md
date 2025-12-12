# Product Management Agent

An AI-powered Product Management Agent built with Google ADK (Agent Development Kit) that helps create comprehensive Product Requirements Documents (PRDs). The agent orchestrates market research, user journey mapping, and PRD generation using a sequential multi-agent workflow.

## Features

- **Market Research**: Uses Google Search to gather external context and validate product ideas
- **User Journey Mapping**: Creates detailed customer personas and user journeys
- **PRD Generation**: Produces comprehensive PRDs with problem statements, user stories, and functional requirements  
- **Duplicate Detection**: Searches for existing similar PRDs before creating new ones (Human-in-the-Loop)
- **User Approval**: Requests confirmation before saving PRDs (Human-in-the-Loop)
- **Cloud Storage**: Stores PRDs in Google Cloud Storage with both markdown and HTML formats
- **Shareable URLs**: Generates public URLs for viewing PRDs as formatted HTML
- **Vertex AI Search**: Enables semantic search across all stored PRDs

## Architecture

The system consists of two main components:

1. **PM Agent** (`pm_agent/`): Multi-agent workflow built with Google ADK
   - `market_researcher_agent`: Conducts market research using Google Search
   - `user_journey_agent`: Creates user personas and journey maps
   - `prd_scripter_agent`: Generates final PRD document
   - `root_agent`: Orchestrates the workflow with duplicate detection and user approval

2. **MCP Server** (`prd_mcp_server/`): Cloud Run service for PRD storage and retrieval
   - Stores PRDs in Google Cloud Storage
   - Converts markdown to HTML for better presentation
   - Integrates with Vertex AI Search for semantic search

## Prerequisites

- Python 3.11 or higher
- Google Cloud Project with:
  - Vertex AI API enabled
  - Cloud Storage API enabled
  - Cloud Run API enabled
  - Discovery Engine API enabled (for Vertex AI Search)
- Google Cloud SDK (gcloud) installed and authenticated
- Google ADK installed: `pip install google-cloud-aiplatform[adk,agent_engines]`

## Quick Start

### 1. Deploy the MCP Server

```bash
cd prd_mcp_server

# Set your configuration
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET_NAME="your-bucket-name"
export DATASTORE_ID="your-datastore-id"

# Update deploy.sh with your values
./deploy.sh

# Configure security permissions
./configure_security.sh
```

The deployment will output the MCP server URL. Save this for the next step.

### 2. Configure the PM Agent

```bash
cd product-management-agent

# Copy environment template
cp .env.example .env
cp pm_agent/.env.example pm_agent/.env

# Edit both .env files with your values:
# - GOOGLE_CLOUD_PROJECT
# - GOOGLE_CLOUD_LOCATION  
# - GOOGLE_CLOUD_STAGING_BUCKET
# - MCP_SERVER_URL (from step 1)
```

### 3. Test Locally

```bash
# Run local web interface
adk web pm_agent --port 8080

# Visit http://localhost:8080 in your browser
# Try: "Create a PRD for a mobile fitness tracking app"
```

### 4. Deploy to Agent Engine

```bash
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --description="AI-powered PM agent that creates comprehensive PRDs" \
  --trace_to_cloud \
  pm_agent
```

### 5. Register to Gemini Enterprise (Optional)

1. Go to [Gemini Enterprise Console](https://console.cloud.google.com/gemini/enterprise)
2. Click "Register Agent"
3. Use the reasoning engine resource name from the deployment output
4. Add custom icon URL: `https://openmoji.org/data/color/svg/1F916.svg`

## Project Structure

```
product-management-agent/
├── pm_agent/
│   ├── agent.py           # Main agent definitions
│   ├── mcp_tool.py         # MCP server integration tools
│   ├── __init__.py
│   ├── .env.example       # Environment template for agent
│   └── requirements.txt    
├── .env.example           # Environment template for root
├── .gitignore
├── requirements.txt
├── README.md
└── docs/
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    └── LOCAL_TESTING.md

prd_mcp_server/
├── server.py              # FastAPI MCP server
├── storage.py             # GCS and Vertex AI Search integration
├── deploy.sh              # Deployment script
├── configure_security.sh  # Security configuration
├── Dockerfile
├── requirements.txt
├── .gitignore
└── README.md
```

## Usage

### Creating a New PRD

1. Provide a product idea to the agent
2. Agent searches for duplicate PRDs
   - If duplicates found: asks if you want to view existing or create new
   - If no duplicates: proceeds to PRD generation
3. Agent conducts market research and creates user journeys
4. Agent presents complete PRD and asks for confirmation
5. Confirm to save the PRD to cloud storage
6. Receive shareable HTML URL for the formatted PRD

### Searching Existing PRDs

Use the `search_existing_prds` tool:
```python
search_existing_prds("fitness app")
```

### Viewing a PRD

Use the `get_prd` tool with a PRD ID:
```python
get_prd("mobile_fitness_tracking_app_1234567890")
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

**MCP Server** (environment variables set in Cloud Run):
```bash
PROJECT_ID=your-project-id
BUCKET_NAME=your-prd-storage-bucket
DATASTORE_ID=your-datastore-id
```

## Development

### Running Tests

```bash
# Test MCP server locally
cd prd_mcp_server
python test_mcp.py

# Test agent locally
cd product-management-agent
adk web pm_agent --port 8080 --reload_agents
```

### Updating the Agent

```bash
# Redeploy after making changes
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --trace_to_cloud \
  pm_agent
```

## Architecture Details

### Sequential Agent Workflow

The PM agent uses a `SequentialAgent` pattern where each sub-agent's output becomes the next agent's input:

1. **Market Researcher** → Gathers external context
2. **User Journey** → Creates personas based on research  
3. **PRD Scripter** → Compiles everything into a PRD

### Human-in-the-Loop (HITL)

Two confirmation points ensure user control:
- **HITL #1**: Duplicate detection - user decides whether to proceed
- **HITL #2**: PRD approval - user confirms before saving

### Dual Format Storage

PRDs are stored in two formats:
- **Markdown (.md)**: Original format for editing and retrieval
- **HTML (.html)**: Formatted version for viewing and search indexing

## Troubleshooting

### Agent can't connect to MCP server
- Verify `MCP_SERVER_URL` is set correctly in `pm_agent/.env`
- Check Cloud Run service is deployed and accessible
- Verify service account has proper IAM permissions

### Search not finding PRDs
- Ensure Vertex AI Search data store is configured
- Check data store is connected to `gs://your-bucket/prds/*.html`
- Wait for initial indexing to complete (can take a few minutes)

### Telemetry not showing in console
- Redeploy with `--trace_to_cloud` flag
- Check Cloud Trace in Google Cloud Console

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

Built with:
- [Google ADK](https://github.com/google/adk)
- [Google Cloud Vertex AI](https://cloud.google.com/vertex-ai)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Markdown](https://python-markdown.github.io/)

## Support

For issues and questions:
- Check the [documentation](./docs/)
- Open an issue on GitHub
- Consult [Google ADK documentation](https://google.github.io/adk-docs/)
