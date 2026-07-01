#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI is required. Install it, then run 'az login' before deploying." >&2
  exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to build the API image locally." >&2
  exit 1
fi

if ! az account show >/dev/null 2>&1; then
  echo "Run 'az login' first so the script can use your connected Azure identity." >&2
  exit 1
fi

if [[ -f .env ]]; then
  set -a
  # Keep the project .env compatible with both local runs and deploy-time overrides.
  source .env
  set +a
fi

: "${AZURE_SUBSCRIPTION_ID:?Set AZURE_SUBSCRIPTION_ID before running the deploy script.}"
: "${RESOURCE_GROUP:?Set RESOURCE_GROUP before running the deploy script.}"
: "${CONTAINERAPPS_ENVIRONMENT:?Set CONTAINERAPPS_ENVIRONMENT before running the deploy script.}"
: "${ACR_NAME:?Set ACR_NAME before running the deploy script.}"
: "${CONTAINER_APP_NAME:?Set CONTAINER_APP_NAME before running the deploy script.}"
: "${API_KEY:?Set API_KEY before running the deploy script.}"

IMAGE_NAME="${IMAGE_NAME:-devops-monitor-api}"
DOCKERFILE_PATH="${DOCKERFILE_PATH:-api/Dockerfile}"
LOCATION="${LOCATION:-westeurope}"
TARGET_PORT="${TARGET_PORT:-8000}"
INGRESS="${INGRESS:-external}"
TAG="${TAG:-latest}"

echo "Using subscription ${AZURE_SUBSCRIPTION_ID}"
az account set --subscription "$AZURE_SUBSCRIPTION_ID"

if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  echo "Creating resource group ${RESOURCE_GROUP} in ${LOCATION}"
  az group create --name "$RESOURCE_GROUP" --location "$LOCATION" >/dev/null
fi

if ! az acr show --name "$ACR_NAME" >/dev/null 2>&1; then
  echo "Creating ACR ${ACR_NAME} in ${LOCATION}"
  az acr create --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --sku Basic --location "$LOCATION" >/dev/null
fi

ACR_LOGIN_SERVER="$(az acr show --name "$ACR_NAME" --query loginServer --output tsv)"
ACR_RESOURCE_ID="$(az acr show --name "$ACR_NAME" --query id --output tsv)"
IMAGE_REFERENCE="${ACR_LOGIN_SERVER}/${IMAGE_NAME}:${TAG}"

echo "Logging into ${ACR_NAME}"
az acr login --name "$ACR_NAME"

echo "Building ${IMAGE_REFERENCE} from ${DOCKERFILE_PATH}"
docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_REFERENCE" .

echo "Pushing ${IMAGE_REFERENCE}"
docker push "$IMAGE_REFERENCE"

if ! az containerapp env show --name "$CONTAINERAPPS_ENVIRONMENT" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  echo "Creating Container Apps environment ${CONTAINERAPPS_ENVIRONMENT}"
  az containerapp env create \
    --name "$CONTAINERAPPS_ENVIRONMENT" \
    --resource-group "$RESOURCE_GROUP" \
    --location "$LOCATION" >/dev/null
fi

if az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then
  echo "Updating existing Container App ${CONTAINER_APP_NAME}"
  az containerapp update \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --image "$IMAGE_REFERENCE" \
    --set-env-vars API_KEY="$API_KEY" >/dev/null
else
  echo "Creating Container App ${CONTAINER_APP_NAME}"
  az containerapp create \
    --name "$CONTAINER_APP_NAME" \
    --resource-group "$RESOURCE_GROUP" \
    --environment "$CONTAINERAPPS_ENVIRONMENT" \
    --image "$IMAGE_REFERENCE" \
    --registry-server "$ACR_LOGIN_SERVER" \
    --registry-identity system \
    --system-assigned \
    --ingress "$INGRESS" \
    --target-port "$TARGET_PORT" \
    --set-env-vars API_KEY="$API_KEY" >/dev/null
fi

APP_PRINCIPAL_ID="$(az containerapp show --name "$CONTAINER_APP_NAME" --resource-group "$RESOURCE_GROUP" --query identity.principalId --output tsv)"
if [[ -n "$APP_PRINCIPAL_ID" && "$APP_PRINCIPAL_ID" != "null" ]]; then
  echo "Granting AcrPull on ${ACR_NAME} to the Container App identity"
  az role assignment create \
    --assignee-object-id "$APP_PRINCIPAL_ID" \
    --assignee-principal-type ServicePrincipal \
    --role AcrPull \
    --scope "$ACR_RESOURCE_ID" >/dev/null 2>&1 || true
fi

echo
echo "Deployment complete."
echo "Container App: ${CONTAINER_APP_NAME}"
echo "Image: ${IMAGE_REFERENCE}"