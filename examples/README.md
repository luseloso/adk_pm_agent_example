# Examples

This directory contains example scripts demonstrating different ways to use and deploy the Product Management Agent.

## Available Examples

### 1. Local Testing (`local_test.py`)

Test the agent structure locally without deployment.

```bash
python examples/local_test.py
```

**Use case**: Verify agent configuration before deploying

### 2. Custom Product Ideas (`custom_product.py`)

Test the deployed agent with various product ideas to see how it generates different PRDs.

```bash
# Set your deployment details
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export REASONING_ENGINE_ID=your-reasoning-engine-id

python examples/custom_product.py
```

**Use case**: Generate PRDs for different product concepts

### 3. Automated Deployment & Testing (`deploy_and_test.py`)

Deploy the agent and immediately test it in one workflow.

```bash
# Configure deployment
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1
export GOOGLE_CLOUD_STAGING_BUCKET=gs://your-staging-bucket

python examples/deploy_and_test.py
```

**Use case**: Quick deployment and validation

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **APIs enabled**:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable cloudtrace.googleapis.com
   gcloud services enable telemetry.googleapis.com
   ```
3. **Python 3.10-3.13** installed
4. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

All examples support configuration via environment variables:

- `GOOGLE_CLOUD_PROJECT` - Your GCP project ID
- `GOOGLE_CLOUD_LOCATION` - Region (default: us-central1)
- `GOOGLE_CLOUD_STAGING_BUCKET` - GCS bucket for staging
- `REASONING_ENGINE_ID` - Deployed agent ID (for testing examples)

You can also use a `.env` file:

```bash
cp .env.example .env
# Edit .env with your values
```

## Example Workflows

### First-time Setup

```bash
# 1. Deploy the agent
python examples/deploy_and_test.py

# 2. Note the REASONING_ENGINE_ID from output

# 3. Test with custom ideas
export REASONING_ENGINE_ID=your-id-from-step-1
python examples/custom_product.py
```

### Development Iteration

```bash
# 1. Test locally after code changes
python examples/local_test.py

# 2. If tests pass, redeploy
python examples/deploy_and_test.py
```

## Sample Output

The PM agent generates comprehensive PRDs through three stages:

1. **Market Research**: Analyzes problem space, identifies target audience, researches competitors
2. **User Journey Mapping**: Creates personas and maps customer journeys
3. **PRD Generation**: Compiles findings into a structured Product Requirements Document

Example PRD sections:
- Problem Statement
- User Stories with acceptance criteria
- Functional Requirements
- Non-functional Requirements

## Troubleshooting

### Error: "Reasoning Engine not found"

Make sure you've deployed the agent and set the correct `REASONING_ENGINE_ID`:

```bash
# List your deployed reasoning engines
gcloud ai reasoning-engines list \
  --project=your-project-id \
  --region=us-central1
```

### Error: "Telemetry API not enabled"

Enable the Telemetry API:

```bash
gcloud services enable telemetry.googleapis.com --project=your-project-id
```

Wait 2-3 minutes after enabling.

### Error: "Permission denied"

Ensure you have the necessary IAM roles:
- `roles/aiplatform.user`
- `roles/storage.objectAdmin` (for staging bucket)

## Next Steps

- Review [Architecture Documentation](../docs/ARCHITECTURE.md)
- Read [Deployment Guide](../docs/DEPLOYMENT.md)
- Explore [ADK Documentation](https://google.github.io/adk-docs/)
