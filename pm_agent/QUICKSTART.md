# Quick Start Guide

Get the Product Management Agent up and running in 5 minutes.

## Prerequisites

1. Google Cloud Project with billing enabled
2. Python 3.10-3.13 installed
3. gcloud CLI installed and authenticated

## Step 1: Enable Required APIs

```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudtrace.googleapis.com
gcloud services enable telemetry.googleapis.com
```

Wait 2-3 minutes after enabling telemetry API.

## Step 2: Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your values
nano .env
```

Set these variables:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket
```

## Step 3: Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

## Step 4: Deploy the Agent

### Option A: Using Python SDK (Recommended)

```bash
python examples/deploy_and_test.py
```

This will:
- Deploy the agent to Vertex AI Agent Engine
- Return a Reasoning Engine ID
- Optionally test it immediately

### Option B: Using ADK CLI

```bash
adk deploy agent_engine \
  --project=$GOOGLE_CLOUD_PROJECT \
  --region=$GOOGLE_CLOUD_LOCATION \
  --staging_bucket=$GOOGLE_CLOUD_STAGING_BUCKET \
  --display_name="pm-agent" \
  --description="Product Management Agent" \
  --trace_to_cloud \
  pm_agent
```

## Step 5: Test the Agent

```bash
# Set the Reasoning Engine ID from deployment
export REASONING_ENGINE_ID=your-reasoning-engine-id

# Run test
python test_agent.py
```

## Step 6: View Results

### Check Traces
Visit Cloud Trace console:
```
https://console.cloud.google.com/traces/list?project=your-project-id
```

### Check Agent Engine
Visit Agent Engine console:
```
https://console.cloud.google.com/vertex-ai/agent-builder/engines?project=your-project-id
```

## Example Usage

Test with a product idea:

```python
import vertexai
from vertexai import agent_engines

# Initialize
vertexai.init(project="your-project", location="us-central1")

# Get deployed agent
agent = agent_engines.get("projects/.../reasoningEngines/YOUR_ID")

# Test with product idea
result = agent.query(
    input="I want to build a mobile app for fitness tracking"
)

print(result)
```

The agent will generate:
1. Market research analysis
2. User personas and journeys
3. Complete PRD with user stories and requirements

## Troubleshooting

### Error: "Telemetry API not enabled"
```bash
gcloud services enable telemetry.googleapis.com --project=your-project-id
```
Wait 2-3 minutes.

### Error: "Python version not supported"
Use Python 3.9-3.13:
```bash
python --version  # Check version
pyenv install 3.13.2  # If needed
```

### Error: "Permission denied"
Ensure you have required IAM roles:
```bash
gcloud projects add-iam-policy-binding your-project-id \
  --member=user:your-email@example.com \
  --role=roles/aiplatform.user
```

## Next Steps

- **Try different product ideas**: `python examples/custom_product.py`
- **Read architecture docs**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Learn about deployment**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Review examples**: [examples/README.md](examples/README.md)

## Support

- [Full README](README.md)
- [Troubleshooting Guide](docs/DEPLOYMENT.md#troubleshooting)
- [ADK Documentation](https://google.github.io/adk-docs/)

---

**Estimated Time**: 5-10 minutes for first deployment
