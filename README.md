# DevOps Monitoring Dashboard

Projet final du cours Python for DevOps : une API FastAPI de monitoring, un dashboard Streamlit, des tests automatisés et un environnement local reproductible avec Docker Compose.

## Architecture

- `api/` : backend FastAPI avec routes `/health`, `/metrics`, `/servers` et WebSocket `/ws/metrics`
- `dashboard/` : interface Streamlit avec onglets métriques et serveurs
- `tests/` : tests unitaires et tests de routes
- `docker-compose.yml` : exécution locale de la stack

## Prérequis

- Python 3.11
- Docker et Docker Compose
- Make

## Installation locale

```bash
cp .env.example .env
make up
make test
```

## Variables d'environnement

- `API_KEY` : clé utilisée par l'API pour protéger les actions sensibles
- `API_BASE_URL` : URL de l'API utilisée par le dashboard, par défaut `http://api:8000`
- `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID` : non requis par l'application actuelle

## Déploiement sans accès Microsoft Entra ID

Le projet ne dépend pas d'un service principal côté développeur. Le déploiement se fait avec l'identité Azure déjà ouverte sur ta machine via `az login`.

Variables nécessaires au déploiement de l'API sur Azure Container Apps:

- `AZURE_SUBSCRIPTION_ID`
- `RESOURCE_GROUP`
- `CONTAINERAPPS_ENVIRONMENT`
- `ACR_NAME`
- `CONTAINER_APP_NAME`
- `API_KEY`
- `IMAGE_NAME` : optionnel, défaut `devops-monitor-api`
- `DOCKERFILE_PATH` : optionnel, défaut `api/Dockerfile`
- `LOCATION` : optionnel, défaut `westeurope`
- `TARGET_PORT` : optionnel, défaut `8000`
- `INGRESS` : optionnel, défaut `external`
- `TAG` : optionnel, défaut `latest`

Commandes prêtes à copier:

```bash
az login
az account set --subscription "$AZURE_SUBSCRIPTION_ID"
export AZURE_SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000"
export RESOURCE_GROUP="rg-devops-monitor"
export CONTAINERAPPS_ENVIRONMENT="cae-devops-monitor"
export ACR_NAME="myregistry"
export CONTAINER_APP_NAME="devops-monitor-api"
export API_KEY="changeme"
make deploy
```

Le script crée ou met à jour le resource group, l'ACR, l'environnement Container Apps et la Container App. Il publie l'image Docker dans ACR avec ton identité Azure CLI, puis active une identité managée sur la Container App.

## Runtime via Managed Identity

L'application FastAPI ne consomme actuellement aucun service Azure au runtime. Il n'y a donc pas de credential Azure à maintenir dans le code applicatif aujourd'hui.

Si tu ajoutes plus tard Key Vault, Blob Storage, Service Bus, Azure OpenAI ou un autre SDK Azure, la bonne approche sera de réutiliser l'identité managée de la Container App. Dans ce cas, `AZURE_CLIENT_ID` resterait uniquement optionnel pour une identité managée utilisateur, mais il n'est pas nécessaire pour le projet actuel.

## Lancement local sans Docker

```bash
source .venv/bin/activate
make dev
```

## Endpoints

- `GET /health`
- `GET /metrics`
- `POST /servers`
- `GET /servers`
- `GET /servers/{id}`
- `DELETE /servers/{id}`
- `POST /servers/{id}/check`
- `WS /ws/metrics`

## Remarques Azure

La partie Azure est maintenant préparée pour un déploiement local avec Azure CLI.
Le workflow GitHub Actions reste centré sur la CI, et le déploiement Azure se fait via `make deploy`.
