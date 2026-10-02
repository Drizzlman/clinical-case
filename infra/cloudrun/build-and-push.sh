#!/usr/bin/env bash
# Build and push all three images to Artifact Registry.
#
# Usage (from the repository root):
#   GCP_PROJECT=my-project GCP_REGION=europe-west1 \
#     NEXT_PUBLIC_API_URL=https://clinical-backend-xxxx.run.app \
#     bash infra/cloudrun/build-and-push.sh
#
# Environment:
#   GCP_PROJECT          (required) GCP project id (or GOOGLE_CLOUD_PROJECT)
#   GCP_REGION           default europe-west1
#   ARTIFACT_REPO        default clinical-case
#   TAG                  default short git SHA (or a timestamp)
#   NEXT_PUBLIC_API_URL  backend URL inlined into the frontend client bundle
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

PROJECT_ID="${GCP_PROJECT:-${GOOGLE_CLOUD_PROJECT:-}}"
REGION="${GCP_REGION:-europe-west1}"
REPO="${ARTIFACT_REPO:-clinical-case}"
TAG="${TAG:-$(git rev-parse --short HEAD 2>/dev/null || date +%Y%m%d%H%M%S)}"
NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:8000}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: set GCP_PROJECT (or GOOGLE_CLOUD_PROJECT)." >&2
  exit 1
fi

REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}"
echo "Project=${PROJECT_ID} Region=${REGION} Repo=${REPO} Tag=${TAG}"

echo "── ensuring Artifact Registry repository exists ──"
if ! gcloud artifacts repositories describe "$REPO" \
  --project "$PROJECT_ID" --location "$REGION" >/dev/null 2>&1; then
  gcloud artifacts repositories create "$REPO" \
    --project "$PROJECT_ID" --location "$REGION" \
    --repository-format docker --description "Clinical case images"
fi

echo "── configuring docker auth for ${REGION}-docker.pkg.dev ──"
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

build_and_push() {
  local dockerfile="$1" image="$2"
  shift 2
  echo "── building ${image} ──"
  docker build -f "$dockerfile" "$@" -t "$image" "$ROOT"
  docker push "$image"
}

build_and_push infra/Dockerfile.backend "${REGISTRY}/backend:${TAG}"
build_and_push infra/Dockerfile.frontend "${REGISTRY}/frontend:${TAG}" \
  --build-arg "NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}"
build_and_push infra/Dockerfile.pipeline "${REGISTRY}/pipeline:${TAG}"

echo ""
echo "PASS. Pushed images:"
echo "  ${REGISTRY}/backend:${TAG}"
echo "  ${REGISTRY}/frontend:${TAG}"
echo "  ${REGISTRY}/pipeline:${TAG}"
