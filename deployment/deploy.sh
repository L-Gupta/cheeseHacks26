#!/bin/bash

# Configuration
PROJECT_ID="your-google-cloud-project-id"
REGION="us-central1"
SERVICE_NAME="ai-followup-backend"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"
DB_INSTANCE_NAME="ai-followup-db"
DB_NAME="followups"
DB_USER="postgres"

echo "Deploying to Google Cloud Run..."

# 1. Build Docker Image
echo "Building image $IMAGE_NAME..."
gcloud builds submit --tag $IMAGE_NAME

# 2. Deploy to Cloud Run
echo "Deploying Cloud Run service..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --add-cloudsql-instances $PROJECT_ID:$REGION:$DB_INSTANCE_NAME \
  --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_LOCATION=$REGION,DATABASE_URL=postgresql+pg8000://$DB_USER:YOUR_PASSWORD@/$DB_NAME?unix_sock=/cloudsql/$PROJECT_ID:$REGION:$DB_INSTANCE_NAME/.s.PGSQL.5432"

# 3. Get the URL
URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)')
echo "Service deployed at: $URL"

# 4. Setup Cloud Scheduler (if not exists)
echo "Setting up Cloud Scheduler to hit $URL/cron/trigger-followups every 15 minutes..."
gcloud scheduler jobs create http trigger-followups-job \
  --schedule="*/15 * * * *" \
  --uri="$URL/cron/trigger-followups" \
  --http-method=POST \
  --location=$REGION \
  || gcloud scheduler jobs update http trigger-followups-job \
  --schedule="*/15 * * * *" \
  --uri="$URL/cron/trigger-followups" \
  --http-method=POST \
  --location=$REGION

echo "Deployment complete."
