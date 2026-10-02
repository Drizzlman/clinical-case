#!/usr/bin/env bash
# Deploy backend + frontend services and the pipeline job to Cloud Run.
#
# Order matters: the frontend image embeds NEXT_PUBLIC_API_URL at build time, so
# deploy the backend first, then rebuild/repush the frontend with the backend URL
# (see docs/en/deployment.md → "Two-pass frontend build").
#
# Usage (from the repository root):
#   GCP_PROJECT=my-project GCP_REGION=europe-west1 TAG=abc123 \
#     DATABASE_URL='postgresql+asyncpg://user:pass@host:5432/db' \
#     bash infra/cloudrun/deploy.sh
#
# Environment:
#   GCP_PROJECT       (required) GCP project id (or GOOGLE_CLOUD_PROJECT)
#   GCP_REGION        default europe-west1
#   ARTIFACT_REPO     default clinical-case
#   TAG               default short git SHA
#   DATABASE_URL      used once to create the Secret Manager secret if absent
#   DATABASE_SECRET   default clinical-database-url
#   CORS_ORIGINS      (required) JSON array of allowed origins, e.g.
#                     '["https://clinical-frontend-xxxx.run.app"]'
#   LLM_MODEL         default gemini-3.8-flash (required by the pipeline job)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${GCP_REGION:-europe-west1}"
REPO="${ARTIFACT_REPO:-clinical-case}"
TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
DATABASE_SECRET="${DATABASE_SECRET:-clinical-database-url}"
CORS_ORIGINS="${CORS_ORIGINS:-}"
BACKEND_SERVICE="${BACKEND_SERVICE:-clinical-backend}"
FRONTEND_SERVICE="${FRONTEND_SERVICE:-clinical-frontend}"
PIPELINE_JOB="${PIPELINE_JOB:-clinical-pipeline}"
LLM_MODEL="${LLM_MODEL:-gemini-3.8-flash}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: set GCP_PROJECT (or GOOGLE_CLOUD_PROJECT)." >&2
  exit 1
fi

if [[ -z "$CORS_ORIGINS" ]]; then
  echo "ERROR: set CORS_ORIGINS to a JSON array of allowed origins, e.g. '[\"https://clinical-frontend-xxxx.run.app\"]'." >&2
  exit 1
fi

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
BACKEND_IMAGE="${BACKEND_IMAGE:-${REGISTRY}/backend:${TAG}}"
FRONTEND_IMAGE="${FRONTEND_IMAGE:-${REGISTRY}/frontend:${TAG}}"
PIPELINE_IMAGE="${PIPELINE_IMAGE:-${REGISTRY}/pipeline:${TAG}}"

echo "── ensuring Secret Manager secret '${DATABASE_SECRET}' ──"
if ! gcloud secrets describe "$DATABASE_SECRET" --project "$PROJECT_ID" >/dev/null 2>&1; then
  if [[ -z "${DATABASE_URL:-}" ]]; then
    echo "ERROR: secret '${DATABASE_SECRET}' is missing and DATABASE_URL is not set." >&2
    echo "Create it manually: printf '%s' 'postgresql+asyncpg://...' | \\" >&2
    echo "  gcloud secrets create ${DATABASE_SECRET} --data-file=- --project ${PROJECT_ID}" >&2
    exit 1
  fi
  printf '%s' "$DATABASE_URL" | gcloud secrets create "$DATABASE_SECRET" \
    --project "$PROJECT_ID" --replication-policy automatic --data-file=-
fi

echo "── deploying backend service '${BACKEND_SERVICE}' ──"
gcloud run deploy "$BACKEND_SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" \
  --image "$BACKEND_IMAGE" \
  --allow-unauthenticated \
  --port 8080 \
  --set-secrets "DATABASE_URL=${DATABASE_SECRET}:latest" \
  --set-env-vars "ENVIRONMENT=production,CORS_ORIGINS=${CORS_ORIGINS}"

BACKEND_URL="$(gcloud run services describe "$BACKEND_SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" \
  --format 'value(status.url)')"
echo "Backend URL: ${BACKEND_URL}"

echo "── deploying frontend service '${FRONTEND_SERVICE}' ──"
echo "NOTE: the frontend image must have been built with NEXT_PUBLIC_API_URL=${BACKEND_URL}"
gcloud run deploy "$FRONTEND_SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" \
  --image "$FRONTEND_IMAGE" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "BACKEND_URL=${BACKEND_URL}"

FRONTEND_URL="$(gcloud run services describe "$FRONTEND_SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" \
  --format 'value(status.url)')"
echo "Frontend URL: ${FRONTEND_URL}"

echo "── deploying pipeline job '${PIPELINE_JOB}' ──"
gcloud run jobs deploy "$PIPELINE_JOB" \
  --project "$PROJECT_ID" --region "$REGION" \
  --image "$PIPELINE_IMAGE" \
  --set-env-vars "GCP_PROJECT=${PROJECT_ID},GCP_LOCATION=${REGION},LLM_MODEL=${LLM_MODEL},LLM_CLIENT=vertex,BACKEND_URL=${BACKEND_URL}"

echo ""
echo "PASS. Verify:"
echo "  curl -fsS ${BACKEND_URL}/health"
echo "  open ${FRONTEND_URL}"
echo "  gcloud run jobs execute ${PIPELINE_JOB} --project ${PROJECT_ID} --region ${REGION} --wait"
