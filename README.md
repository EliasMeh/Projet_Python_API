# DevOps Monitoring Dashboard

Projet final du cours Python for DevOps : une API FastAPI de monitoring, un dashboard Streamlit, des tests automatisés et un environnement local reproductible avec Docker Compose.

Déploiement actuel : l'application est hébergée sur Azure Web App et accessible ici : https://projetapielias-agc2gsa7a4fvfkfm.polandcentral-01.azurewebsites.net

## Architecture

- `api/` : backend FastAPI avec routes `/health`, `/metrics`, `/servers` et WebSocket `/ws/metrics`
- `dashboard/` : interface Streamlit, déployée comme webapp
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

## Déploiement actuel sur Azure Web App

Le projet est aujourd'hui déployé sur Azure Web App. L'URL publique est : https://projetapielias-agc2gsa7a4fvfkfm.polandcentral-01.azurewebsites.net

Le workflow principal de déploiement reste [.github/workflows/main_projetapielias.yml](.github/workflows/main_projetapielias.yml), qui pousse l'application vers Azure Web App.

Le fichier [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) est conservé volontairement avec ce nom pour un transfert futur vers AKS. Il ne correspond pas au chemin de production actuel.

Variables historiques liées à l'ancien déploiement Azure Container Apps:

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

Ce bloc reflète l'ancien chemin de déploiement Container Apps du projet. Il reste utile comme référence si tu dois réutiliser l'architecture Azure avec une containerisation complète, mais ce n'est plus le chemin utilisé pour l'URL Web App ci-dessus.

## Pipeline GitHub Actions

Le workflow [.github/workflows/main_projetapielias.yml](.github/workflows/main_projetapielias.yml) assure le build et le déploiement sur Azure Web App.

Le workflow [.github/workflows/ci-cd.yml](.github/workflows/ci-cd.yml) est maintenu pour une migration éventuelle vers AKS :

- `test` sur chaque push et pull request
- `build` sur `main` pour construire et pousser les images Docker vers ACR
- `deploy` sur `main` pour appliquer les manifests Kubernetes sur AKS

Secrets GitHub attendus pour la partie déploiement:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`
- `ACR_NAME`
- `RESOURCE_GROUP`
- `CONTAINERAPPS_ENVIRONMENT`
- `API_KEY`

Variables GitHub optionnelles pour personnaliser les noms d'images ou d'applications:

- `API_IMAGE_NAME`
- `DASHBOARD_IMAGE_NAME`
- `API_APP_NAME`
- `DASHBOARD_APP_NAME`
- `API_BASE_URL`

Si tu n'as pas encore ces secrets, garde le script local `make deploy` comme voie manuelle de déploiement historique pour Container Apps.

## Si tu utilises Azure App Service au lieu de Container Apps

Le message "Hey, Python developers! Your app service is up and running." indique que tu es sur un App Service Python par défaut, pas sur l'API FastAPI du projet.

Dans ce cas, le startup command à mettre dans le portail Azure est:

```bash
gunicorn --bind=0.0.0.0:8000 --workers=1 --worker-class uvicorn.workers.UvicornWorker api.main:app
```

Points à vérifier:

- l'application doit être déployée depuis le contenu du repo, pas seulement créer un App Service vide
- `gunicorn` est maintenant présent dans `requirements.txt`
- l'application doit écouter sur le port attendu par App Service, ici `8000`
- si Azure fournit une variable `PORT`, tu peux aussi adapter la commande avec `--bind=0.0.0.0:$PORT`

Si tu déploies en container personnalisé sur App Service, garde plutôt le startup command vide et laisse le `CMD` du Dockerfile lancer `uvicorn`.

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

La partie Azure est maintenant préparée pour un déploiement local avec Azure CLI et pour un déploiement GitHub Actions plus proche du sujet.
