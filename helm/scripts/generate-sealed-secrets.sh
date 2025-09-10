#!/bin/bash

# Script to generate sealed secrets for the genascope-backend
# This script helps convert plain text secrets to encrypted sealed secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="default"
SCOPE="strict"
OUTPUT_FILE=""
INTERACTIVE=false

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Generate sealed secrets for genascope-backend"
    echo ""
    echo "Options:"
    echo "  -n, --namespace NAMESPACE    Target namespace (default: default)"
    echo "  -s, --scope SCOPE           Encryption scope: strict|namespace-wide|cluster-wide (default: strict)"
    echo "  -o, --output FILE           Output file for encrypted values"
    echo "  -i, --interactive           Interactive mode - prompt for secret values"
    echo "  -h, --help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -n development -i                           # Interactive mode for development namespace"
    echo "  $0 -n production -o sealed-secrets-prod.yaml   # Generate for production"
    echo "  $0 --namespace staging --scope namespace-wide   # Generate for staging with namespace scope"
}

# Function to check if kubeseal is installed
check_kubeseal() {
    if ! command -v kubeseal &> /dev/null; then
        echo -e "${RED}Error: kubeseal is not installed${NC}"
        echo "Please install kubeseal: https://github.com/bitnami-labs/sealed-secrets#installation"
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

# Function to encrypt a secret value
encrypt_secret() {
    local key=$1
    local value=$2
    local namespace=$3
    local scope=$4
    
    echo -n "$value" | kubeseal --raw --from-file=$key=/dev/stdin --name=genascope-backend-secrets --namespace="$namespace" --scope="$scope"
}

# Function to prompt for secret value
prompt_secret() {
    local key=$1
    local description=$2
    local optional=$3
    
    echo -e "${YELLOW}Enter $description${NC}"
    if [ "$optional" = "true" ]; then
        echo -e "${YELLOW}(Optional - press Enter to skip)${NC}"
    fi
    
    read -s -p "$key: " value
    echo ""
    
    if [ -z "$value" ] && [ "$optional" = "false" ]; then
        echo -e "${RED}Error: $key is required${NC}"
        exit 1
    fi
    
    echo "$value"
}

# Function to generate sealed secrets interactively
generate_interactive() {
    local namespace=$1
    local scope=$2
    
    echo -e "${GREEN}Generating sealed secrets for namespace: $namespace${NC}"
    echo -e "${GREEN}Encryption scope: $scope${NC}"
    echo ""
    
    # Required secrets
    echo -e "${YELLOW}=== Required Secrets ===${NC}"
    
    postgres_password=$(prompt_secret "postgres-password" "PostgreSQL password" false)
    secret_key=$(prompt_secret "secret-key" "Application secret key" false)
    openai_api_key=$(prompt_secret "openai-api-key" "OpenAI API key" false)
    
    # Optional secrets
    echo ""
    echo -e "${YELLOW}=== Optional Secrets ===${NC}"
    
    lab_api_key=$(prompt_secret "lab-api-key" "Lab API key" true)
    smtp_password=$(prompt_secret "smtp-password" "SMTP password" true)
    
    echo ""
    echo -e "${GREEN}Encrypting secrets...${NC}"
    
    # Encrypt required secrets
    encrypted_postgres=$(encrypt_secret "postgres-password" "$postgres_password" "$namespace" "$scope")
    encrypted_secret_key=$(encrypt_secret "secret-key" "$secret_key" "$namespace" "$scope")
    encrypted_openai=$(encrypt_secret "openai-api-key" "$openai_api_key" "$namespace" "$scope")
    
    # Create output
    output="# Encrypted secrets for namespace: $namespace"$'\n'
    output+="# Generated on: $(date)"$'\n'
    output+="# Scope: $scope"$'\n'
    output+=""$'\n'
    output+="sealedSecrets:"$'\n'
    output+="  enabled: true"$'\n'
    output+="  encryptedData:"$'\n'
    output+="    postgres-password: \"$encrypted_postgres\""$'\n'
    output+="    secret-key: \"$encrypted_secret_key\""$'\n'
    output+="    openai-api-key: \"$encrypted_openai\""$'\n'
    
    # Encrypt optional secrets if provided
    if [ -n "$lab_api_key" ]; then
        encrypted_lab=$(encrypt_secret "lab-api-key" "$lab_api_key" "$namespace" "$scope")
        output+="    lab-api-key: \"$encrypted_lab\""$'\n'
    fi
    
    if [ -n "$smtp_password" ]; then
        encrypted_smtp=$(encrypt_secret "smtp-password" "$smtp_password" "$namespace" "$scope")
        output+="    smtp-password: \"$encrypted_smtp\""$'\n'
    fi
    
    echo "$output"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        -s|--scope)
            SCOPE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -i|--interactive)
            INTERACTIVE=true
            shift
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

# Validate scope
if [[ ! "$SCOPE" =~ ^(strict|namespace-wide|cluster-wide)$ ]]; then
    echo -e "${RED}Error: Invalid scope '$SCOPE'. Must be one of: strict, namespace-wide, cluster-wide${NC}"
    exit 1
fi

# Check prerequisites
check_kubeseal
check_kubectl

echo -e "${GREEN}Genascope Backend Sealed Secrets Generator${NC}"
echo "=========================================="

if [ "$INTERACTIVE" = "true" ]; then
    # Generate secrets interactively
    output=$(generate_interactive "$NAMESPACE" "$SCOPE")
    
    if [ -n "$OUTPUT_FILE" ]; then
        echo "$output" > "$OUTPUT_FILE"
        echo -e "${GREEN}Encrypted secrets saved to: $OUTPUT_FILE${NC}"
    else
        echo ""
        echo -e "${GREEN}Encrypted secrets (copy to your values file):${NC}"
        echo "================================================"
        echo "$output"
    fi
else
    echo -e "${YELLOW}Use --interactive flag to generate secrets interactively${NC}"
    echo "Example: $0 --namespace $NAMESPACE --interactive"
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Copy the encrypted values to your values file"
echo "2. Deploy with: helm upgrade --install genascope-backend . -f values-sealed-secrets.yaml"
echo "3. The sealed-secrets controller will decrypt the secrets automatically"
