# Deployment Guide

This guide covers deploying the Product Management Agent to Vertex AI Agent Engine.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **APIs enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable cloudtrace.googleapis.com
   gcloud services enable telemetry.googleapis.com
   ```
3. **Python 3.10-3.13** installed
4. **Google Cloud SDK** installed and configured

## Deployment Options

### Option 1: ADK CLI (Recommended)

```bash
# Set environment variables
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket

# Deploy with tracing enabled
adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --staging_bucket=$GOOGLE_CLOUD_STAGING_BUCKET \
  --display_name="pm-agent" \
  --description="Product Management multi-agent system" \
  --trace_to_cloud \
  pm_agent
```

### Option 2: Python SDK

```python
import vertexai
from vertexai.preview import reasoning_engines
from pm_agent.agent import root_agent

# Initialize
vertexai.init(
    project="your-project-id",
    location="us-central1",
    staging_bucket="gs://your-bucket"
)

# Create ADK app
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True
)

# Deploy
remote_app = reasoning_engines.ReasoningEngine.create(
    reasoning_engine=app,
    requirements=["google-cloud-aiplatform[adk,agent_engines]>=1.112"],
    extra_packages=["pm_agent/agent.py"],
    sys_version="3.13"
)

print(f"Deployed: {remote_app.resource_name}")
```

## Post-Deployment

### Verify Deployment

```bash
# List reasoning engines
gcloud ai reasoning-engines list \
  --project=your-project-id \
  --region=us-central1
```

### Test the Agent

```bash
python test_agent.py
```

### View Traces

Visit Cloud Trace console:
```
https://console.cloud.google.com/traces/list?project=your-project-id
```

## Troubleshooting

### Error: Telemetry API not enabled

```bash
gcloud services enable telemetry.googleapis.com --project=your-project-id
```

Wait 2-3 minutes after enabling.

### Error: Python version not supported

Ensure you're using Python 3.9-3.13. Check with:
```bash
python --version
```

### Error: Payload size too large

This happens if venv/ directories are included. Use `.gitignore` to exclude them or deploy from a clean directory.

## Configuration

### Environment Variables

Set these in `.env` file:

```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket
```

### Memory Configuration

Memory is configured in the agent with VertexAiMemoryBankService:

```python
from google.adk.memory import VertexAiMemoryBankService

def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project="your-project",
        location="us-central1"
    )
```

## Production Considerations

1. **Resource Limits**: Set appropriate quotas for your project
2. **Monitoring**: Enable Cloud Logging and Tracing
3. **Cost Management**: Monitor API usage and set budgets
4. **Security**: Use IAM roles to control access
5. **Versioning**: Tag deployments with version numbers

## Next Steps

- Review [Architecture](ARCHITECTURE.md)
- See [Examples](../examples/)
- Read [ADK Documentation](https://google.github.io/adk-docs/)
