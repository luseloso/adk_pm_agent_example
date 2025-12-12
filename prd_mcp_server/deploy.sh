#!/bin/bash
set -e

# Configuration - Update these values for your project
PROJECT_ID="${PROJECT_ID:-your-project-id}"
REGION="${REGION:-us-central1}"
BUCKET_NAME="${BUCKET_NAME:-your-prd-storage}"
DATASTORE_ID="${DATASTORE_ID:-your-datastore-id}"
SERVICE_NAME="${SERVICE_NAME:-prd-mcp-server}"

echo "========================================="
echo "Deploying PRD MCP Server to Cloud Run"
echo "========================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"
echo "Datastore: $DATASTORE_ID"
echo ""

# 1. Create GCS bucket for PRD storage
echo "Step 1: Creating GCS bucket..."
if gcloud storage buckets describe gs://$BUCKET_NAME --project=$PROJECT_ID 2>/dev/null; then
    echo "  ✓ Bucket already exists"
else
    gcloud storage buckets create gs://$BUCKET_NAME \
        --project=$PROJECT_ID \
        --location=$REGION \
        --uniform-bucket-level-access
    echo "  ✓ Bucket created"
fi

# 2. Create Vertex AI Search Data Store
echo "Step 2: Creating Vertex AI Search data store..."
echo "    - Go to https://console.cloud.google.com/gen-app-builder/engines"
echo "    - Create a new search app with ID: $DATASTORE_ID"
echo "    - Connect it to gs://$BUCKET_NAME/prds/*.html"
echo ""

# 3. Deploy MCP Server to Cloud Run
echo "Step 3: Deploying MCP server to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --source . \
    --project=$PROJECT_ID \
    --region=$REGION \
    --no-allow-unauthenticated \
    --set-env-vars=BUCKET_NAME=$BUCKET_NAME,DATASTORE_ID=$DATASTORE_ID,PROJECT_ID=$PROJECT_ID \
    --memory=512Mi \
    --cpu=1 \
    --timeout=60 \
    --max-instances=10

echo "  ✓ MCP server deployed"

# 4. Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(status.url)')

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo "Service URL: $SERVICE_URL"
echo ""
echo "Next Steps:"
echo "1. Configure service account permissions (run configure_security.sh)"
echo "2. Update PM agent .env with MCP_SERVER_URL=$SERVICE_URL"
echo "3. Configure Vertex AI Search data store if not done automatically"
echo "   - Link GCS bucket: gs://$BUCKET_NAME/prds/*"
echo "========================================="
