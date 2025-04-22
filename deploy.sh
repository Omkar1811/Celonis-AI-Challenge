#!/bin/bash

# Set your project ID
PROJECT_ID="your-project-id"

# Set Redis instance info
REDIS_INSTANCE_NAME="twitter-cache"
REDIS_TIER="basic"
REDIS_VERSION="redis_6_x"
REDIS_REGION="us-central1"

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting deployment process...${NC}"

# Create Redis instance if it doesn't exist
echo -e "${YELLOW}Checking if Redis instance exists...${NC}"
if ! gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REDIS_REGION --project=$PROJECT_ID &>/dev/null; then
    echo -e "${YELLOW}Creating Redis instance...${NC}"
    gcloud redis instances create $REDIS_INSTANCE_NAME \
        --region=$REDIS_REGION \
        --zone=${REDIS_REGION}-a \
        --tier=$REDIS_TIER \
        --size=1 \
        --redis-version=$REDIS_VERSION \
        --project=$PROJECT_ID
    
    echo -e "${GREEN}Redis instance created!${NC}"
else
    echo -e "${GREEN}Redis instance already exists!${NC}"
fi

# Get Redis host and port
echo -e "${YELLOW}Getting Redis connection details...${NC}"
REDIS_HOST=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REDIS_REGION --project=$PROJECT_ID --format="value(host)")
REDIS_PORT=$(gcloud redis instances describe $REDIS_INSTANCE_NAME --region=$REDIS_REGION --project=$PROJECT_ID --format="value(port)")

echo -e "${GREEN}Redis connection details:${NC}"
echo "Host: $REDIS_HOST"
echo "Port: $REDIS_PORT"

# Build and deploy using Cloud Build
echo -e "${YELLOW}Submitting Cloud Build job...${NC}"
gcloud builds submit --project $PROJECT_ID --config cloudbuild.yaml \
    --substitutions=_REDIS_HOST=$REDIS_HOST,_REDIS_PORT=$REDIS_PORT

# Get the service URL
echo -e "${YELLOW}Getting deployed service URL...${NC}"
SERVICE_URL=$(gcloud run services describe twitter-support-chatbot \
    --platform managed \
    --region us-central1 \
    --project $PROJECT_ID \
    --format 'value(status.url)')

echo -e "${GREEN}Service deployed successfully!${NC}"
echo "Service URL: $SERVICE_URL"
echo "API Endpoints:"
echo "- Health Check: $SERVICE_URL/health"
echo "- Generate Response: $SERVICE_URL/generate_response"
echo "- Chat: $SERVICE_URL/chat"
echo "- New Session: $SERVICE_URL/new_session" 