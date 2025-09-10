# Sealed Secrets Implementation Guide

This guide explains how to use Sealed Secrets with the Genascope Backend Helm chart for secure GitOps workflows.

## Overview

Sealed Secrets allow you to encrypt your Kubernetes secrets and store them safely in Git repositories. The encrypted secrets can only be decrypted by the Sealed Secrets controller running in your cluster.

## Prerequisites

1. **Sealed Secrets Controller**: Install the Sealed Secrets controller in your cluster:
   ```bash
   kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml
   ```

2. **kubeseal CLI**: Install the kubeseal command-line tool:
   ```bash
   # macOS
   brew install kubeseal
   
   # Linux
   wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-0.24.0-linux-amd64.tar.gz
   tar -xvzf kubeseal-0.24.0-linux-amd64.tar.gz kubeseal
   sudo install -m 755 kubeseal /usr/local/bin/kubeseal
   ```

## Quick Start

### 1. Generate Encrypted Secrets

Use the provided script to generate encrypted secrets interactively:

```bash
cd helm/scripts
./generate-sealed-secrets.sh --namespace development --interactive
```

This will prompt you for:
- PostgreSQL password (required)
- Application secret key (required)
- OpenAI API key (required)
- Lab API key (optional)
- SMTP password (optional)

### 2. Update Values File

Copy the generated encrypted values to your values file or use the provided `values-sealed-secrets.yaml`:

```yaml
sealedSecrets:
  enabled: true
  encryptedData:
    postgres-password: "AgBy3i4OJSWK+PiTySYZZA9rO6HcOcw=="
    secret-key: "AgAKV7ha9q8SZvwKn3YQKf9nO3ScMpZ=="
    openai-api-key: "AgBm2kL8vQ5RJfxNp1WaEr8dP2HbNsX=="
    # ... other encrypted secrets
```

### 3. Deploy with Sealed Secrets

Use the deployment script:

```bash
cd helm/scripts
./deploy-sealed-secrets.sh --namespace development
```

Or deploy manually:

```bash
helm upgrade --install genascope-backend ./helm/genascope-backend \
  --namespace development \
  --values ./helm/genascope-backend/values-sealed-secrets.yaml \
  --wait
```

## Manual Secret Generation

If you prefer to generate secrets manually:

### Basic Command Structure

```bash
echo -n "your-secret-value" | kubeseal --raw \
  --from-file=/dev/stdin \
  --name=genascope-backend-secrets \
  --namespace=your-namespace \
  --scope=strict \
  --key=secret-key-name
```

### Example Commands

```bash
# PostgreSQL password
echo -n "mydbpassword" | kubeseal --raw \
  --from-file=/dev/stdin \
  --name=genascope-backend-secrets \
  --namespace=development \
  --scope=strict \
  --key=postgres-password

# Application secret key
echo -n "mysecretkey123" | kubeseal --raw \
  --from-file=/dev/stdin \
  --name=genascope-backend-secrets \
  --namespace=development \
  --scope=strict \
  --key=secret-key

# OpenAI API key
echo -n "sk-..." | kubeseal --raw \
  --from-file=/dev/stdin \
  --name=genascope-backend-secrets \
  --namespace=development \
  --scope=strict \
  --key=openai-api-key
```

## Security Scopes

Sealed Secrets support three encryption scopes:

### 1. Strict (Recommended)
- **Scope**: `strict`
- **Binding**: Specific namespace and secret name
- **Usage**: Most secure, secrets can only be decrypted in the exact namespace with the exact name
- **Example**: Perfect for production environments

### 2. Namespace-wide
- **Scope**: `namespace-wide`
- **Binding**: Specific namespace, any secret name
- **Usage**: Secrets can be decrypted in any secret within the namespace
- **Example**: Useful for development environments

### 3. Cluster-wide
- **Scope**: `cluster-wide`
- **Binding**: Any namespace, any secret name
- **Usage**: Least secure, secrets can be decrypted anywhere in the cluster
- **Example**: Generally not recommended

## Environment-Specific Configurations

### Development Environment

```bash
# Generate secrets for development
./generate-sealed-secrets.sh --namespace development --scope namespace-wide --interactive

# Deploy to development
./deploy-sealed-secrets.sh --namespace development --values-file values-sealed-secrets.yaml
```

### Staging Environment

```bash
# Generate secrets for staging
./generate-sealed-secrets.sh --namespace staging --scope strict --interactive --output sealed-secrets-staging.yaml

# Deploy to staging
./deploy-sealed-secrets.sh --namespace staging --values-file sealed-secrets-staging.yaml
```

### Production Environment

```bash
# Generate secrets for production
./generate-sealed-secrets.sh --namespace production --scope strict --interactive --output sealed-secrets-production.yaml

# Deploy to production
./deploy-sealed-secrets.sh --namespace production --values-file sealed-secrets-production.yaml
```

## Migration from External Secrets

If you're currently using external secrets (like `pgvector-secret`), follow these steps:

### 1. Extract Current Secret Values

```bash
# Get current database password
kubectl get secret pgvector-secret -n development -o jsonpath='{.data.postgres-password}' | base64 -d

# Get other secrets as needed
kubectl get secret your-openai-secret -n development -o jsonpath='{.data.api-key}' | base64 -d
```

### 2. Generate Sealed Secrets

Use the extracted values with the generation script:

```bash
./generate-sealed-secrets.sh --namespace development --interactive
```

### 3. Update Deployment

Switch from external secrets to sealed secrets:

```bash
# Deploy with sealed secrets
./deploy-sealed-secrets.sh --namespace development

# Verify deployment
kubectl get pods -n development -l app.kubernetes.io/instance=genascope-backend
```

### 4. Clean Up (Optional)

After verifying the deployment works with sealed secrets:

```bash
# Remove old external secrets (be careful!)
kubectl delete secret pgvector-secret -n development
kubectl delete secret your-openai-secret -n development
```

## Troubleshooting

### Common Issues

1. **kubeseal command not found**
   ```bash
   # Install kubeseal
   brew install kubeseal  # macOS
   # or download from GitHub releases for other platforms
   ```

2. **Sealed Secrets controller not found**
   ```bash
   # Install the controller
   kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml
   
   # Verify installation
   kubectl get pods -n kube-system -l name=sealed-secrets-controller
   ```

3. **Cannot decrypt sealed secret**
   - Check that the namespace, secret name, and scope match exactly
   - Verify the Sealed Secrets controller is running
   - Check controller logs: `kubectl logs -n kube-system -l name=sealed-secrets-controller`

4. **Permission denied errors**
   ```bash
   # Make scripts executable
   chmod +x helm/scripts/*.sh
   ```

### Debugging Commands

```bash
# Check sealed secret status
kubectl get sealedsecrets -n development

# Check if secret was created
kubectl get secrets -n development genascope-backend-secrets

# View sealed secret details
kubectl describe sealedsecret genascope-backend-sealed-secret -n development

# Check controller logs
kubectl logs -n kube-system -l name=sealed-secrets-controller

# Test deployment with dry run
./deploy-sealed-secrets.sh --namespace development --dry-run
```

## Best Practices

1. **Use strict scope for production** - Provides the highest security
2. **Store encrypted values in Git** - Safe to commit encrypted sealed secrets
3. **Regular key rotation** - Rotate your secret values periodically
4. **Backup encryption keys** - Keep sealed-secrets controller backup
5. **Environment separation** - Use different namespaces/clusters for different environments
6. **Audit access** - Monitor who can generate sealed secrets
7. **Test deployments** - Always test with `--dry-run` first

## Script Reference

### generate-sealed-secrets.sh

```bash
# Usage
./generate-sealed-secrets.sh [OPTIONS]

# Options
-n, --namespace NAMESPACE    # Target namespace (default: default)
-s, --scope SCOPE           # Encryption scope (default: strict)
-o, --output FILE           # Output file for encrypted values
-i, --interactive           # Interactive mode - prompt for secret values
-h, --help                  # Show help message

# Examples
./generate-sealed-secrets.sh -n development -i
./generate-sealed-secrets.sh -n production -o prod-secrets.yaml
./generate-sealed-secrets.sh --namespace staging --scope namespace-wide
```

### deploy-sealed-secrets.sh

```bash
# Usage
./deploy-sealed-secrets.sh [OPTIONS]

# Options
-n, --namespace NAMESPACE    # Target namespace (default: default)
-r, --release RELEASE        # Helm release name (default: genascope-backend)
-f, --values-file FILE       # Values file to use (default: values-sealed-secrets.yaml)
-c, --chart-dir DIR          # Chart directory (default: .)
--dry-run                    # Perform a dry run without deploying
--no-wait                    # Don't wait for deployment to complete
--timeout TIMEOUT           # Timeout for deployment (default: 300s)
-h, --help                   # Show help message

# Examples
./deploy-sealed-secrets.sh -n development
./deploy-sealed-secrets.sh -n production -f values-prod-sealed.yaml
./deploy-sealed-secrets.sh --dry-run
```

## GitOps Workflow

With Sealed Secrets, you can safely store encrypted secrets in Git:

```yaml
# .github/workflows/deploy.yml
name: Deploy with Sealed Secrets

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Kubernetes
        run: |
          # Install helm
          curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar -xzO linux-amd64/helm > /usr/local/bin/helm
          chmod +x /usr/local/bin/helm
          
          # Deploy with sealed secrets
          helm upgrade --install genascope-backend ./helm/genascope-backend \
            --namespace production \
            --values ./helm/genascope-backend/values-sealed-secrets-prod.yaml \
            --wait
```

This approach enables true GitOps workflows where all configuration, including secrets, are stored in Git repositories securely.
