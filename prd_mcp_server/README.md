# PRD MCP Server

Model Context Protocol (MCP) server for Product Requirements Document (PRD) storage and retrieval using Google Cloud Run, Cloud Storage, and Vertex AI Search.

## Features

- **PRD Storage**: Store PRDs as markdown files in Google Cloud Storage
- **Full-Text Search**: Semantic search powered by Vertex AI Search (Discovery Engine)
- **MCP Protocol**: Standard Model Context Protocol over Server-Sent Events
- **Secure**: IAM-based authentication via Cloud Run
- **Scalable**: Serverless deployment on Cloud Run

## Architecture

```
Client (PM Agent)
      │
      ├─ search_existing_prds() ────┐
      ├─ get_prd()                   │
      └─ store_prd()                 │
                                     ▼
                        ┌────────────────────────┐
                        │ MCP Server             │
                        │ (Cloud Run)            │
                        │                        │
                        │ - FastAPI + SSE        │
                        │ - MCP Protocol         │
                        └────────────┬───────────┘
                                     │
                 ┌───────────────────┼───────────────────┐
                 │                   │                   │
                 ▼                   ▼                   ▼
        ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐
        │ Cloud Storage  │  │ Vertex AI      │  │ IAM/Security    │
        │ (PRD Files)    │  │ Search         │  │ (Auth)          │
        └────────────────┘  └────────────────┘  └─────────────────┘
```

## MCP Tools

### 1. search_existing_prds
Search for existing PRDs using full-text semantic search.

**Input**:
```json
{
  "query": "mobile app for fitness tracking"
}
```

**Output**:
```json
{
  "query": "mobile app for fitness tracking",
  "results_count": 2,
  "results": [
    {
      "prd_id": "fitness_tracker_1234567890",
      "product_name": "Fitness Tracker App",
      "summary": "A mobile application for tracking workouts...",
      "snippet": "...focused on helping users track their fitness goals...",
      "created_at": "2025-12-09T10:30:00",
      "relevance_score": 0.95
    }
  ]
}
```

### 2. get_prd
Retrieve the full content of a specific PRD by ID.

**Input**:
```json
{
  "prd_id": "fitness_tracker_1234567890"
}
```

**Output**:
```json
{
  "prd_id": "fitness_tracker_1234567890",
  "content": "# Fitness Tracker App\n\n## Problem Statement\n...",
  "product_name": "Fitness Tracker App",
  "created_at": "2025-12-09T10:30:00",
  "summary": "A mobile application for tracking workouts...",
  "gcs_path": "gs://your-prd-storage/prds/fitness_tracker_1234567890.md"
}
```

### 3. store_prd
Store a new PRD to Cloud Storage.

**Input**:
```json
{
  "product_name": "New Product",
  "content": "# Product Requirements Document\n\n## Problem Statement\n...",
  "metadata": {
    "author": "PM Agent",
    "version": "1.0"
  }
}
```

**Output**:
```json
{
  "prd_id": "new_product_1234567890",
  "gcs_path": "gs://your-prd-storage/prds/new_product_1234567890.md",
  "product_name": "New Product",
  "created_at": "2025-12-09T11:00:00",
  "summary": "..."
}
```

## Deployment

### Prerequisites

- Google Cloud Project with billing enabled
- gcloud CLI installed and authenticated
- Docker (optional, for local testing)

### Deploy to Cloud Run

```bash
chmod +x deploy.sh
./deploy.sh
```

This will:
1. Create GCS bucket `your-prd-storage`
2. Create Vertex AI Search data store `prd-search-datastore`
3. Deploy MCP server to Cloud Run
4. Configure environment variables

### Configure Security

```bash
chmod +x configure_security.sh
./configure_security.sh
```

This will:
1. Create service account `pm-agent-sa`
2. Grant Cloud Run invoker permission
3. Grant Storage object admin permission
4. Grant Discovery Engine editor permission

### Configure Vertex AI Search

If the data store wasn't created automatically:

1. Go to [Vertex AI Search Console](https://console.cloud.google.com/gen-app-builder/engines)
2. Create a new search app:
   - **ID**: `prd-search-datastore`
   - **Industry**: Generic
   - **Content**: Unstructured documents
3. Import data from GCS:
   - **Bucket**: `gs://your-prd-storage/prds/*`
   - **Data schema**: Content
   - **Reconciliation mode**: Incremental

## Local Testing

### Run locally with Docker

```bash
docker build -t prd-mcp-server .
docker run -p 8080:8080 \
  -e BUCKET_NAME=your-prd-storage \
  -e DATASTORE_ID=prd-search-datastore \
  -e PROJECT_ID=your-project-id \
  -v ~/.config/gcloud:/root/.config/gcloud \
  prd-mcp-server
```

### Run with Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export BUCKET_NAME=your-prd-storage
export DATASTORE_ID=prd-search-datastore
export PROJECT_ID=your-project-id

python server.py
```

### Test endpoints

```bash
# Health check
curl http://localhost:8080/health

# List tools
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'

# Search PRDs
curl -X POST http://localhost:8080/sse \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "search_existing_prds",
      "arguments": {"query": "mobile app"}
    }
  }'
```

## Environment Variables

- `BUCKET_NAME`: GCS bucket for PRD storage (default: `your-prd-storage`)
- `DATASTORE_ID`: Vertex AI Search data store ID (default: `prd-search-datastore`)
- `PROJECT_ID`: Google Cloud project ID (default: `your-project-id`)
- `PORT`: Server port (default: `8080`)

## Integration with PM Agent

Add to `product-management-agent/.env`:

```bash
MCP_SERVER_URL=https://prd-mcp-server-[hash]-uc.a.run.app
```

The PM agent will use this URL to communicate with the MCP server for PRD operations.

## Security

- **Authentication**: Cloud Run IAM authentication (no public access)
- **Service Account**: `pm-agent-sa@your-project-id.iam.gserviceaccount.com`
- **Permissions**:
  - `roles/run.invoker` - Invoke Cloud Run service
  - `roles/storage.objectAdmin` - Read/write GCS objects
  - `roles/discoveryengine.editor` - Search and index PRDs

## Monitoring

View logs:
```bash
gcloud run services logs read prd-mcp-server \
  --project=your-project-id \
  --region=us-central1 \
  --limit=50
```

## Troubleshooting

### Search not working

If Vertex AI Search is not returning results:
1. Check data store status in Console
2. Verify GCS bucket is linked correctly
3. Wait for initial indexing (can take 10-30 minutes)
4. Check IAM permissions for Discovery Engine

The server includes a fallback to simple GCS keyword matching if Vertex AI Search fails.

### Authentication errors

Ensure service account has all required permissions:
```bash
gcloud projects get-iam-policy your-project-id \
  --flatten="bindings[].members" \
  --filter="bindings.members:pm-agent-sa@your-project-id.iam.gserviceaccount.com"
```

## References

- [Model Context Protocol](https://modelcontextprotocol.io/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs/enterprise-search-introduction)
- [MCP on Cloud Run Guide](https://docs.cloud.google.com/run/docs/host-mcp-servers)
