#!/bin/bash
set -e

PROJECT_ID="your-project-id"
SA_NAME="pm-agent-sa"
SA_EMAIL="$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com"
SERVICE_NAME="prd-mcp-server"
REGION="us-central1"
BUCKET_NAME="your-prd-storage"

echo "========================================="
echo "Configuring Security for PRD MCP Server"
echo "========================================="

# 1. Create service account
echo "Step 1: Creating service account..."
if gcloud iam service-accounts describe $SA_EMAIL --project=$PROJECT_ID 2>/dev/null; then
    echo "  ✓ Service account already exists"
else
    gcloud iam service-accounts create $SA_NAME \
        --project=$PROJECT_ID \
        --display-name="PM Agent Service Account" \
        --description="Service account for PM Agent to access MCP server and GCS"
    echo "  ✓ Service account created"
fi

# 2. Grant Cloud Run invoker permission (for MCP client)
echo "Step 2: Granting Cloud Run invoker permission..."
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.invoker" \
    --region=$REGION \
    --project=$PROJECT_ID
echo "  ✓ Cloud Run invoker permission granted"

# 3. Grant GCS access (for PRD storage)
echo "Step 3: Granting GCS storage access..."
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin" \
    --project=$PROJECT_ID
echo "  ✓ GCS storage permission granted"

# 4. Grant Discovery Engine access (for PRD search)
echo "Step 4: Granting Discovery Engine access..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/discoveryengine.editor"
echo "  ✓ Discovery Engine permission granted"

# 5. Update Cloud Run service to use the service account
echo "Step 5: Updating Cloud Run service to use service account..."
gcloud run services update $SERVICE_NAME \
    --service-account=$SA_EMAIL \
    --region=$REGION \
    --project=$PROJECT_ID
echo "  ✓ Cloud Run service updated"

echo ""
echo "========================================="
echo "Security Configuration Complete!"
echo "========================================="
echo "Service Account: $SA_EMAIL"
echo ""
echo "Permissions granted:"
echo "  ✓ roles/run.invoker (Cloud Run)"
echo "  ✓ roles/storage.objectAdmin (GCS)"
echo "  ✓ roles/discoveryengine.editor (Vertex AI Search)"
echo ""
echo "Next Steps:"
echo "1. Configure your PM agent to use this service account"
echo "2. Test authentication with MCP server"
echo "========================================="
