# Deployment Guide

Complete deployment guide for the PM Agent and MCP Server.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **APIs enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable discoveryengine.googleapis.com
   ```
3. **Python 3.11+** installed
4. **Google Cloud SDK** (`gcloud`) installed and configured

## Part 1: Deploy MCP Server

The MCP server must be deployed first, as the PM Agent requires its URL.

### 1.1 Navigate to MCP Server Directory

```bash
cd prd_mcp_server
```

### 1.2 Configure Environment

Edit the deployment script or export variables:

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET_NAME="your-prd-storage"
export DATASTORE_ID="your-datastore-id"
export SERVICE_NAME="prd-mcp-server"
```

### 1.3 Deploy to Cloud Run

```bash
./deploy.sh
```

This script will:
- Create GCS bucket for PRD storage
- Create Vertex AI Search data store
- Build and deploy Docker container to Cloud Run
- Configure environment variables

Save the MCP server URL from the output (format: `https://SERVICE_NAME-PROJECT_NUMBER.REGION.run.app`)

### 1.4 Configure Security

```bash
# Edit configure_security.sh with your values
./configure_security.sh
```

This sets up:
- Service account for the PM Agent
- IAM permissions for Cloud Run, GCS, and Vertex AI Search
- Cloud Run service authentication

## Part 2: Deploy PM Agent

### 2.1 Configure Environment

```bash
cd ../pm_agent

# Copy environment template
cp .env.example .env

# Edit .env with your values:
# - GOOGLE_CLOUD_PROJECT
# - GOOGLE_CLOUD_LOCATION
# - GOOGLE_CLOUD_STAGING_BUCKET
# - MCP_SERVER_URL (from Part 1)
```

### 2.2 Deploy with ADK CLI

```bash
adk deploy agent_engine \
  --project=your-project-id \
  --region=us-central1 \
  --staging_bucket=gs://your-staging-bucket \
  --display_name="Product Management Agent" \
  --description="AI PM agent with sequential workflow and HITL" \
  --trace_to_cloud \
  pm_agent
```

The deployment will:
- Package the agent code
- Upload to staging bucket
- Create Reasoning Engine on Vertex AI
- Enable Cloud Trace

Save the resource name from the output for registration.

## Part 3: Verify Deployment

### 3.1 Test MCP Server

```bash
curl https://YOUR_MCP_SERVER_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "prd-mcp-server",
  "bucket": "your-prd-storage",
  "datastore": "your-datastore-id"
}
```

### 3.2 List Reasoning Engines

```bash
gcloud ai reasoning-engines list \
  --project=your-project-id \
  --region=us-central1
```

### 3.3 View Traces

Visit Cloud Trace in Google Cloud Console:
```
https://console.cloud.google.com/traces/list?project=your-project-id
```

## Part 4: Register to Gemini Enterprise (Optional)

1. Navigate to [Gemini Enterprise Console](https://console.cloud.google.com/gemini/enterprise)
2. Click "Register Agent"
3. Enter the reasoning engine resource name
4. Configure:
   - Display Name: "Product Management Agent"
   - Description: "AI-powered PM agent"
   - Icon URL: `https://openmoji.org/data/color/svg/1F916.svg`

## Troubleshooting

### MCP Server Not Accessible

**Error**: Connection refused or 403 Forbidden

**Solution**: Check service account permissions
```bash
# Verify Cloud Run service
gcloud run services describe prd-mcp-server \
  --region=us-central1 \
  --project=your-project-id

# Check IAM policy
gcloud run services get-iam-policy prd-mcp-server \
  --region=us-central1 \
  --project=your-project-id
```

### Agent Deployment Fails

**Error**: "Telemetry API not enabled"

**Solution**:
```bash
gcloud services enable telemetry.googleapis.com --project=your-project-id
```

Wait 2-3 minutes after enabling, then retry deployment.

**Error**: "Payload size too large"

**Solution**: Ensure virtual environments are excluded via `.gitignore`

### Vertex AI Search Not Indexing

**Issue**: PRDs not appearing in search results

**Solution**:
1. Check data store configuration points to `gs://your-bucket/prds/*.html`
2. Allow 10-15 minutes for initial indexing
3. Verify HTML files exist in GCS:
   ```bash
   gcloud storage ls gs://your-bucket/prds/
   ```

## Production Considerations

1. **Quotas**: Set appropriate quotas for Vertex AI and Cloud Run
2. **Monitoring**: Enable Cloud Logging and set up alerts
3. **Cost Management**: Monitor API usage and set budgets
4. **Security**: Use least-privilege IAM roles
5. **Backup**: Enable versioning on GCS bucket

## Updating the Agent

After making code changes:

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

The new version will replace the existing deployment.

## Next Steps

- Review [Architecture Documentation](ARCHITECTURE.md)
- See [Local Testing Guide](LOCAL_TESTING.md)
- Explore [Examples](../examples/)

## References

- [ADK Deployment](https://google.github.io/adk-docs/deploy/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Vertex AI Search](https://cloud.google.com/generative-ai-app-builder/docs)
