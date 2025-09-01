#!/bin/bash
set -e

# Genascope Backend Helm Deployment Script
# Usage: ./deploy.sh [environment] [release-name] [namespace]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHART_DIR="$SCRIPT_DIR/genascope-backend"

# Default values
ENVIRONMENT="${1:-dev}"
RELEASE_NAME="${2:-genascope-backend}"
NAMESPACE="${3:-genascope-$ENVIRONMENT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    case "$ENVIRONMENT" in
        dev|staging|prod)
            print_status "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            print_error "Invalid environment: $ENVIRONMENT"
            print_error "Valid environments: dev, staging, prod"
            exit 1
            ;;
    esac
}

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v helm &> /dev/null; then
        print_error "Helm is not installed. Please install Helm 3.0+"
        exit 1
    fi
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl"
        exit 1
    fi
    
    # Check kubectl connectivity
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig"
        exit 1
    fi
    
    print_success "All dependencies are available"
}

# Check if namespace exists, create if not
ensure_namespace() {
    print_status "Checking namespace: $NAMESPACE"
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        print_warning "Namespace $NAMESPACE does not exist. Creating..."
        kubectl create namespace "$NAMESPACE"
        print_success "Namespace $NAMESPACE created"
    else
        print_status "Namespace $NAMESPACE already exists"
    fi
}

# Validate Helm chart
validate_chart() {
    print_status "Validating Helm chart..."
    
    if ! helm lint "$CHART_DIR" &> /dev/null; then
        print_error "Helm chart validation failed"
        helm lint "$CHART_DIR"
        exit 1
    fi
    
    print_success "Helm chart validation passed"
}

# Get secrets for environment
get_secrets() {
    print_status "Setting up secrets for $ENVIRONMENT environment..."
    
    case "$ENVIRONMENT" in
        dev)
            # Development secrets (non-sensitive defaults)
            DATABASE_PASSWORD="${DATABASE_PASSWORD:-dev-password}"
            SECRET_KEY="${SECRET_KEY:-dev-secret-key-change-in-production}"
            OPENAI_API_KEY="${OPENAI_API_KEY:-sk-dev-key}"
            LAB_API_KEY="${LAB_API_KEY:-dev-lab-key}"
            SMTP_PASSWORD="${SMTP_PASSWORD:-dev-smtp-password}"
            ;;
        staging|prod)
            # Production/Staging secrets (must be provided)
            if [[ -z "$DATABASE_PASSWORD" ]]; then
                print_error "DATABASE_PASSWORD environment variable is required for $ENVIRONMENT"
                exit 1
            fi
            if [[ -z "$SECRET_KEY" ]]; then
                print_error "SECRET_KEY environment variable is required for $ENVIRONMENT"
                exit 1
            fi
            if [[ -z "$OPENAI_API_KEY" ]]; then
                print_error "OPENAI_API_KEY environment variable is required for $ENVIRONMENT"
                exit 1
            fi
            ;;
    esac
    
    print_success "Secrets configured for $ENVIRONMENT"
}

# Deploy with Helm
deploy() {
    print_status "Deploying $RELEASE_NAME to $NAMESPACE namespace..."
    
    VALUES_FILE="$CHART_DIR/values-$ENVIRONMENT.yaml"
    
    if [[ ! -f "$VALUES_FILE" ]]; then
        print_error "Values file not found: $VALUES_FILE"
        exit 1
    fi
    
    # Build Helm command
    HELM_CMD="helm upgrade --install $RELEASE_NAME $CHART_DIR"
    HELM_CMD="$HELM_CMD --namespace $NAMESPACE"
    HELM_CMD="$HELM_CMD --values $VALUES_FILE"
    HELM_CMD="$HELM_CMD --wait --timeout 10m"
    
    # Add secrets
    HELM_CMD="$HELM_CMD --set secrets.databasePassword=$DATABASE_PASSWORD"
    HELM_CMD="$HELM_CMD --set secrets.secretKey=$SECRET_KEY"
    HELM_CMD="$HELM_CMD --set secrets.openaiApiKey=$OPENAI_API_KEY"
    
    if [[ -n "$LAB_API_KEY" ]]; then
        HELM_CMD="$HELM_CMD --set secrets.labApiKey=$LAB_API_KEY"
    fi
    
    if [[ -n "$SMTP_PASSWORD" ]]; then
        HELM_CMD="$HELM_CMD --set secrets.smtpPassword=$SMTP_PASSWORD"
    fi
    
    # Add image tag if provided
    if [[ -n "$IMAGE_TAG" ]]; then
        HELM_CMD="$HELM_CMD --set image.tag=$IMAGE_TAG"
        print_status "Using image tag: $IMAGE_TAG"
    fi
    
    # Execute deployment
    print_status "Executing: $HELM_CMD"
    eval "$HELM_CMD"
    
    print_success "Deployment completed successfully!"
}

# Post-deployment checks
post_deploy_checks() {
    print_status "Running post-deployment checks..."
    
    # Wait for pods to be ready
    print_status "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=genascope-backend -n "$NAMESPACE" --timeout=300s
    
    # Check deployment status
    kubectl get deployments -n "$NAMESPACE" -l app.kubernetes.io/name=genascope-backend
    kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=genascope-backend
    
    # Test health endpoint if possible
    print_status "Testing health endpoint..."
    if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
        INGRESS_HOST=$(kubectl get ingress -n "$NAMESPACE" -o jsonpath='{.items[0].spec.rules[0].host}' 2>/dev/null || echo "")
        if [[ -n "$INGRESS_HOST" ]]; then
            print_status "Health check URL: https://$INGRESS_HOST/health"
        fi
    fi
    
    print_success "Post-deployment checks completed"
}

# Show deployment info
show_info() {
    print_success "Deployment Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  Release: $RELEASE_NAME"
    echo "  Namespace: $NAMESPACE"
    echo "  Chart: $CHART_DIR"
    echo ""
    print_status "To check the deployment:"
    echo "  kubectl get all -n $NAMESPACE"
    echo ""
    print_status "To view logs:"
    echo "  kubectl logs -f deployment/$RELEASE_NAME -n $NAMESPACE"
    echo ""
    print_status "To port-forward for local access:"
    echo "  kubectl port-forward svc/$RELEASE_NAME 8080:80 -n $NAMESPACE"
    echo "  Then visit: http://localhost:8080/health"
}

# Print usage
usage() {
    echo "Usage: $0 [environment] [release-name] [namespace]"
    echo ""
    echo "Arguments:"
    echo "  environment   Target environment (dev, staging, prod) [default: dev]"
    echo "  release-name  Helm release name [default: genascope-backend]"
    echo "  namespace     Kubernetes namespace [default: genascope-\$environment]"
    echo ""
    echo "Environment Variables:"
    echo "  DATABASE_PASSWORD  Database password (required for staging/prod)"
    echo "  SECRET_KEY         Application secret key (required for staging/prod)"
    echo "  OPENAI_API_KEY     OpenAI API key (required for staging/prod)"
    echo "  LAB_API_KEY        Lab API key (optional)"
    echo "  SMTP_PASSWORD      SMTP password (optional)"
    echo "  IMAGE_TAG          Docker image tag (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 dev                           # Deploy to development"
    echo "  $0 staging                       # Deploy to staging"
    echo "  $0 prod genascope-prod          # Deploy to production with custom release name"
    echo "  IMAGE_TAG=v1.2.0 $0 prod       # Deploy specific version to production"
}

# Main execution
main() {
    print_status "Starting Genascope Backend deployment..."
    print_status "Environment: $ENVIRONMENT, Release: $RELEASE_NAME, Namespace: $NAMESPACE"
    echo ""
    
    validate_environment
    check_dependencies
    validate_chart
    ensure_namespace
    get_secrets
    deploy
    post_deploy_checks
    show_info
    
    print_success "Deployment process completed successfully! 🚀"
}

# Handle help flag
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    usage
    exit 0
fi

# Run main function
main
