#!/bin/bash

# Simple script to manually encrypt individual secrets
# Usage: ./manual-encrypt.sh <namespace> <secret-key> <secret-value>

set -e

if [ $# -ne 3 ]; then
    echo "Usage: $0 <namespace> <secret-key> <secret-value>"
    echo ""
    echo "Examples:"
    echo "  $0 dev postgres-password 'mydbpassword'"
    echo "  $0 dev secret-key 'my-secret-key-123'"
    echo "  $0 dev openai-api-key 'sk-...'"
    echo ""
    exit 1
fi

NAMESPACE=$1
SECRET_KEY=$2
SECRET_VALUE=$3

echo "Encrypting secret '$SECRET_KEY' for namespace '$NAMESPACE'..."

ENCRYPTED=$(echo -n "$SECRET_VALUE" | kubeseal --raw \
    --from-file=$SECRET_KEY=/dev/stdin \
    --name=genascope-backend-secrets \
    --namespace="$NAMESPACE" \
    --scope=strict)

echo ""
echo "Encrypted value:"
echo "    $SECRET_KEY: \"$ENCRYPTED\""
echo ""
echo "Copy this line to your values file under sealedSecrets.encryptedData"
