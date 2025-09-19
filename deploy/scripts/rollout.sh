#!/usr/bin/env bash
#
# NexusRAG Deployment Rollout Script
# Usage: ./rollout.sh <strategy> <cloud> <action>
#   strategy: rolling | canary | bluegreen
#   cloud:    aws | oci
#   action:   apply | status | promote | rollback
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DIR="${SCRIPT_DIR}/../k8s"
NAMESPACE="nexus-rag"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
log_ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

usage() {
  cat <<USAGE
NexusRAG Deployment Rollout

Usage:
  $(basename "$0") <strategy> <cloud> <action>

Strategies:
  rolling     Standard rolling update via Deployments
  canary      Gradual traffic shift via Argo Rollouts
  bluegreen   Blue/green swap via Argo Rollouts

Clouds:
  aws         Deploy to AWS EKS
  oci         Deploy to OCI OKE

Actions:
  apply       Apply the kustomize manifests to the cluster
  status      Check rollout / deployment status
  promote     Promote a canary or bluegreen rollout
  rollback    Rollback to previous revision

Examples:
  $(basename "$0") rolling aws apply
  $(basename "$0") canary oci status
  $(basename "$0") bluegreen aws promote
USAGE
  exit 1
}

resolve_overlay() {
  local strategy="$1"
  local cloud="$2"

  case "${strategy}" in
    rolling)   echo "${K8S_DIR}/overlays/${cloud}" ;;
    canary)    echo "${K8S_DIR}/overlays/${cloud}-canary" ;;
    bluegreen) echo "${K8S_DIR}/overlays/${cloud}-bluegreen" ;;
    *)         log_error "Unknown strategy: ${strategy}"; exit 1 ;;
  esac
}

validate_prerequisites() {
  local cmds=("kubectl" "kustomize")
  if [[ "$STRATEGY" != "rolling" ]]; then
    cmds+=("kubectl-argo-rollouts")
  fi

  for cmd in "${cmds[@]}"; do
    if ! command -v "$cmd" &>/dev/null; then
      if [[ "$cmd" == "kubectl-argo-rollouts" ]]; then
        log_warn "Argo Rollouts kubectl plugin not found. Install it for canary/bluegreen operations."
        log_warn "Falling back to kubectl for status checks."
      else
        log_error "Required command not found: ${cmd}"
        exit 1
      fi
    fi
  done

  if ! kubectl cluster-info &>/dev/null; then
    log_error "Cannot connect to Kubernetes cluster. Check your kubeconfig."
    exit 1
  fi
}

do_apply() {
  local overlay_dir="$1"
  log_info "Applying manifests from: ${overlay_dir}"

  if [[ ! -d "${overlay_dir}" ]]; then
    log_error "Overlay directory not found: ${overlay_dir}"
    exit 1
  fi

  kustomize build "${overlay_dir}" | kubectl apply -f - --namespace="${NAMESPACE}"
  log_ok "Manifests applied successfully."

  log_info "Waiting for rollout to stabilize..."
  if [[ "$STRATEGY" == "rolling" ]]; then
    kubectl rollout status deployment/nexus-gateway -n "${NAMESPACE}" --timeout=300s || true
    kubectl rollout status deployment/nexus-data-api -n "${NAMESPACE}" --timeout=300s || true
    kubectl rollout status deployment/nexus-ui -n "${NAMESPACE}" --timeout=300s || true
  else
    if command -v kubectl-argo-rollouts &>/dev/null; then
      kubectl argo rollouts status nexus-gateway -n "${NAMESPACE}" --timeout 300 || true
      kubectl argo rollouts status nexus-data-api -n "${NAMESPACE}" --timeout 300 || true
    else
      log_warn "Argo Rollouts plugin not available. Use 'kubectl get rollouts -n ${NAMESPACE}' to check status."
    fi
  fi

  log_ok "Deployment complete."
}

do_status() {
  log_info "Checking deployment status in namespace: ${NAMESPACE}"

  if [[ "$STRATEGY" == "rolling" ]]; then
    kubectl get deployments -n "${NAMESPACE}" -o wide
    echo ""
    kubectl get pods -n "${NAMESPACE}" -o wide
  else
    if command -v kubectl-argo-rollouts &>/dev/null; then
      kubectl argo rollouts list rollouts -n "${NAMESPACE}"
      echo ""
      kubectl argo rollouts status nexus-gateway -n "${NAMESPACE}" || true
      kubectl argo rollouts status nexus-data-api -n "${NAMESPACE}" || true
    else
      kubectl get rollouts -n "${NAMESPACE}" -o wide 2>/dev/null || \
        kubectl get deployments -n "${NAMESPACE}" -o wide
    fi
    echo ""
    kubectl get pods -n "${NAMESPACE}" -o wide
  fi

  echo ""
  kubectl get svc -n "${NAMESPACE}"
  echo ""
  kubectl get ingress -n "${NAMESPACE}" 2>/dev/null || true
}

do_promote() {
  if [[ "$STRATEGY" == "rolling" ]]; then
    log_warn "Promote is not applicable for rolling strategy."
    exit 0
  fi

  log_info "Promoting rollouts in namespace: ${NAMESPACE}"

  if ! command -v kubectl-argo-rollouts &>/dev/null; then
    log_error "Argo Rollouts kubectl plugin required for promote action."
    exit 1
  fi

  kubectl argo rollouts promote nexus-gateway -n "${NAMESPACE}"
  log_ok "Gateway rollout promoted."

  kubectl argo rollouts promote nexus-data-api -n "${NAMESPACE}"
  log_ok "Data API rollout promoted."
}

do_rollback() {
  log_info "Rolling back deployments in namespace: ${NAMESPACE}"

  if [[ "$STRATEGY" == "rolling" ]]; then
    kubectl rollout undo deployment/nexus-gateway -n "${NAMESPACE}"
    kubectl rollout undo deployment/nexus-data-api -n "${NAMESPACE}"
    kubectl rollout undo deployment/nexus-ui -n "${NAMESPACE}"
    log_ok "Rolling update rollback initiated."
  else
    if ! command -v kubectl-argo-rollouts &>/dev/null; then
      log_error "Argo Rollouts kubectl plugin required for rollback action."
      exit 1
    fi

    kubectl argo rollouts abort nexus-gateway -n "${NAMESPACE}"
    kubectl argo rollouts abort nexus-data-api -n "${NAMESPACE}"
    log_ok "Argo Rollout abort initiated. Previous stable version will be restored."
  fi
}

# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

if [[ $# -lt 3 ]]; then
  usage
fi

STRATEGY="$1"
CLOUD="$2"
ACTION="$3"

if [[ ! "$STRATEGY" =~ ^(rolling|canary|bluegreen)$ ]]; then
  log_error "Invalid strategy: ${STRATEGY}"
  usage
fi

if [[ ! "$CLOUD" =~ ^(aws|oci)$ ]]; then
  log_error "Invalid cloud: ${CLOUD}"
  usage
fi

if [[ ! "$ACTION" =~ ^(apply|status|promote|rollback)$ ]]; then
  log_error "Invalid action: ${ACTION}"
  usage
fi

OVERLAY_DIR="$(resolve_overlay "${STRATEGY}" "${CLOUD}")"

log_info "Strategy: ${STRATEGY} | Cloud: ${CLOUD} | Action: ${ACTION}"
log_info "Overlay: ${OVERLAY_DIR}"

validate_prerequisites

case "${ACTION}" in
  apply)    do_apply "${OVERLAY_DIR}" ;;
  status)   do_status ;;
  promote)  do_promote ;;
  rollback) do_rollback ;;
esac
