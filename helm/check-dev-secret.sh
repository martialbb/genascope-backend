#!/bin/bash

# Script to verify pgvector-secret has all required keys for development
NAMESPACE=${1:-dev}
SECRET_NAME="pgvector-secret"

echo "🔍 Checking pgvector-secret in namespace: $NAMESPACE"
echo ""

# Check if secret exists
if ! kubectl get secret $SECRET_NAME -n $NAMESPACE &>/dev/null; then
    echo "❌ Secret '$SECRET_NAME' not found in namespace '$NAMESPACE'"
    echo ""
    echo "To create the secret, run:"
    echo "kubectl create secret generic $SECRET_NAME -n $NAMESPACE \\"
    echo "  --from-literal=postgres-password='your-postgres-password' \\"
    echo "  --from-literal=secret-key='your-secret-key' \\"
    echo "  --from-literal=openai-api-key='your-openai-api-key' \\"
    echo "  --from-literal=lab-api-key='your-lab-api-key' \\"
    echo "  --from-literal=smtp-password='your-smtp-password'"
    exit 1
fi

echo "✅ Secret '$SECRET_NAME' found"
echo ""

# Check required keys
REQUIRED_KEYS=("postgres-password" "secret-key" "openai-api-key")
OPTIONAL_KEYS=("lab-api-key" "smtp-password")

echo "🔑 Checking required keys:"
for key in "${REQUIRED_KEYS[@]}"; do
    if kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath="{.data.$key}" &>/dev/null && \
       [ -n "$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath="{.data.$key}")" ]; then
        echo "  ✅ $key: present"
    else
        echo "  ❌ $key: missing or empty"
        MISSING_REQUIRED=true
    fi
done

echo ""
echo "🔑 Checking optional keys:"
for key in "${OPTIONAL_KEYS[@]}"; do
    if kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath="{.data.$key}" &>/dev/null && \
       [ -n "$(kubectl get secret $SECRET_NAME -n $NAMESPACE -o jsonpath="{.data.$key}")" ]; then
        echo "  ✅ $key: present"
    else
        echo "  ⚠️  $key: missing (optional)"
    fi
done

echo ""

if [ "$MISSING_REQUIRED" = true ]; then
    echo "❌ Some required keys are missing. Please update the secret:"
    echo ""
    echo "# To add missing keys:"
    for key in "${REQUIRED_KEYS[@]}"; do
        echo "kubectl patch secret $SECRET_NAME -n $NAMESPACE -p '{\"data\":{\"$key\":\"$(echo -n 'your-value' | base64)\"}}'"
    done
    exit 1
else
    echo "🎉 All required keys are present in pgvector-secret!"
    echo ""
    echo "You can now deploy with:"
    echo "helm install genascope-backend ./helm/genascope-backend \\"
    echo "  -f ./helm/genascope-backend/values-dev.yaml \\"
    echo "  -n $NAMESPACE"
fi
