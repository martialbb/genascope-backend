#!/bin/bash

# Script to deploy genascope-backend with sealed secrets
# This script handles the deployment process including sealed secrets validation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="default"
RELEASE_NAME="genascope-backend"
VALUES_FILE="../genascope-backend/values-sealed-secrets.yaml"
CHART_DIR="../genascope-backend"
DRY_RUN=false
WAIT=true
TIMEOUT="300s"

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deploy genascope-backend with sealed secrets"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAMESPACE    Target namespace (default: default)"
    echo "  -r, --release RELEASE        Helm release name (default: genascope-backend)"
    echo "  -f, --values-file FILE       Values file to use (default: ../genascope-backend/values-sealed-secrets.yaml)"
    echo "  -c, --chart-dir DIR          Chart directory (default: ../genascope-backend)"
    echo "  --dry-run                    Perform a dry run without actually deploying"
    echo "  --no-wait                    Don't wait for deployment to complete"
    echo "  --timeout TIMEOUT           Timeout for deployment (default: 300s)"
    echo "  -h, --help                   Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -n development                                        # Deploy to development namespace"
    echo "  $0 -n production -f ../genascope-backend/values-prod-sealed.yaml    # Deploy to production with specific values"
    echo "  $0 --dry-run                                             # Test deployment without applying"
}

# Function to check if helm is installed
check_helm() {
    if ! command -v helm &> /dev/null; then
        echo -e "${RED}Error: helm is not installed${NC}"
        echo "Please install helm: https://helm.sh/docs/intro/install/"
        exit 1
    fi
}

# Function to check if kubectl is configured
check_kubectl() {
    if ! kubectl cluster-info &> /dev/null; then
        echo -e "${RED}Error: kubectl is not configured or cluster is not accessible${NC}"
        exit 1
    fi
}

# Function to check if sealed-secrets controller is installed
check_sealed_secrets_controller() {
    if ! kubectl get deployment sealed-secrets-controller -n kube-system &> /dev/null; then
        echo -e "${YELLOW}Warning: Sealed Secrets controller not found in kube-system namespace${NC}"
        echo -e "${YELLOW}Please install it with:${NC}"
        echo "kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Sealed Secrets controller found${NC}"
    fi
}

# Function to validate values file
validate_values_file() {
    local values_file=$1
    
    if [ ! -f "$values_file" ]; then
        echo -e "${RED}Error: Values file '$values_file' not found${NC}"
        exit 1
    fi
    
    # Check if sealed secrets are enabled
    if ! grep -A 2 "sealedSecrets:" "$values_file" | grep -q "enabled: true"; then
        echo -e "${YELLOW}Warning: Sealed secrets don't appear to be enabled in $values_file${NC}"
    fi
    
    echo -e "${GREEN}✓ Values file validated${NC}"
}

# Function to create namespace if it doesn't exist
ensure_namespace() {
    local namespace=$1
    
    if ! kubectl get namespace "$namespace" &> /dev/null; then
        echo -e "${BLUE}Creating namespace: $namespace${NC}"
        kubectl create namespace "$namespace"
    else
        echo -e "${GREEN}✓ Namespace '$namespace' exists${NC}"
    fi
}

# Function to check if release exists
check_release_exists() {
    local release_name=$1
    local namespace=$2
    
    if helm list -n "$namespace" | grep -q "^$release_name"; then
        return 0  # exists
    else
        return 1  # doesn't exist
    fi
}

# Function to deploy the application
deploy_application() {
    local namespace=$1
    local release_name=$2
    local values_file=$3
    local chart_dir=$4
    local dry_run=$5
    local wait=$6
    local timeout=$7
    
    local helm_command="helm"
    local action=""
    
    if check_release_exists "$release_name" "$namespace"; then
        action="upgrade"
        echo -e "${BLUE}Upgrading existing release '$release_name'${NC}"
    else
        action="install"
        echo -e "${BLUE}Installing new release '$release_name'${NC}"
    fi
    
    # Build helm command
    helm_command+=" $action $release_name $chart_dir"
    helm_command+=" --namespace $namespace"
    helm_command+=" --values $values_file"
    
    if [ "$dry_run" = "true" ]; then
        helm_command+=" --dry-run"
    fi
    
    if [ "$wait" = "true" ] && [ "$dry_run" = "false" ]; then
        helm_command+=" --wait --timeout $timeout"
    fi
    
    echo -e "${BLUE}Executing: $helm_command${NC}"
    echo ""
    
    # Execute the helm command
    if eval "$helm_command"; then
        if [ "$dry_run" = "false" ]; then
            echo ""
            echo -e "${GREEN}✓ Deployment successful!${NC}"
        else
            echo ""
            echo -e "${GREEN}✓ Dry run completed successfully${NC}"
        fi
    else
        echo -e "${RED}✗ Deployment failed${NC}"
        exit 1
    fi
}

# Function to display post-deployment information
show_post_deployment_info() {
    local namespace=$1
    local release_name=$2
    
    echo ""
    echo -e "${GREEN}=== Post-Deployment Information ===${NC}"
    echo ""
    
    # Show release status
    echo -e "${BLUE}Release Status:${NC}"
    helm status "$release_name" -n "$namespace"
    echo ""
    
    # Show pods
    echo -e "${BLUE}Pods:${NC}"
    kubectl get pods -n "$namespace" -l "app.kubernetes.io/instance=$release_name"
    echo ""
    
    # Show services
    echo -e "${BLUE}Services:${NC}"
    kubectl get services -n "$namespace" -l "app.kubernetes.io/instance=$release_name"
    echo ""
    
    # Show sealed secrets
    echo -e "${BLUE}Sealed Secrets:${NC}"
    kubectl get sealedsecrets -n "$namespace" -l "app.kubernetes.io/instance=$release_name" 2>/dev/null || echo "No sealed secrets found"
    echo ""
    
    # Show regular secrets (created by sealed secrets)
    echo -e "${BLUE}Secrets (created by Sealed Secrets):${NC}"
    kubectl get secrets -n "$namespace" -l "app.kubernetes.io/instance=$release_name" 2>/dev/null || echo "No secrets found"
    echo ""
    
    # Show ingress
    echo -e "${BLUE}Ingress:${NC}"
    kubectl get ingress -n "$namespace" -l "app.kubernetes.io/instance=$release_name" 2>/dev/null || echo "No ingress found"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -r|--release)
            RELEASE_NAME="$2"
            shift 2
            ;;
        -f|--values-file)
            VALUES_FILE="$2"
            shift 2
            ;;
        -c|--chart-dir)
            CHART_DIR="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --no-wait)
            WAIT=false
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Main execution
echo -e "${GREEN}Genascope Backend Sealed Secrets Deployment${NC}"
echo "=============================================="
echo -e "${BLUE}Namespace:${NC} $NAMESPACE"
echo -e "${BLUE}Release:${NC} $RELEASE_NAME"
echo -e "${BLUE}Values File:${NC} $VALUES_FILE"
echo -e "${BLUE}Chart Directory:${NC} $CHART_DIR"
echo -e "${BLUE}Dry Run:${NC} $DRY_RUN"
echo ""

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"
check_helm
check_kubectl
check_sealed_secrets_controller
validate_values_file "$VALUES_FILE"

# Ensure namespace exists
if [ "$DRY_RUN" = "false" ]; then
    ensure_namespace "$NAMESPACE"
fi

# Deploy the application
echo ""
echo -e "${BLUE}Starting deployment...${NC}"
deploy_application "$NAMESPACE" "$RELEASE_NAME" "$VALUES_FILE" "$CHART_DIR" "$DRY_RUN" "$WAIT" "$TIMEOUT"

# Show post-deployment information
if [ "$DRY_RUN" = "false" ]; then
    show_post_deployment_info "$NAMESPACE" "$RELEASE_NAME"
    
    echo ""
    echo -e "${GREEN}=== Next Steps ===${NC}"
    echo "1. Verify the application is running:"
    echo "   kubectl get pods -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME"
    echo ""
    echo "2. Check the logs:"
    echo "   kubectl logs -n $NAMESPACE -l app.kubernetes.io/instance=$RELEASE_NAME"
    echo ""
    echo "3. Port forward to test locally:"
    echo "   kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME 8000:80"
    echo ""
    echo "4. Access the application:"
    echo "   curl http://localhost:8000/health"
fi
