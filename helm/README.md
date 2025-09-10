# Genascope Backend Helm Chart

This Helm chart deploys the Genascope Backend application, an AI-powered genetic counseling platform, to a Kubernetes cluster.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PostgreSQL database (external or via subchart)
- Redis cache (optional, external or via subchart)

## Installation

### Quick Start (Development)

**Prerequisites for Development:**
The development environment expects an existing secret called `pgvector-secret` in the target namespace with the following keys:
- `postgres-password`: PostgreSQL password
- `secret-key`: Application secret key
- `openai-api-key`: OpenAI API key
- `lab-api-key`: Lab API key (optional)
- `smtp-password`: SMTP password (optional)

**Check if the secret exists:**
```bash
# Check the secret in dev namespace
./helm/check-dev-secret.sh dev
```

**Create the secret if needed:**
```bash
kubectl create secret generic pgvector-secret -n dev \
  --from-literal=postgres-password='your-postgres-password' \
  --from-literal=secret-key='your-secret-key' \
  --from-literal=openai-api-key='your-openai-api-key' \
  --from-literal=lab-api-key='your-lab-api-key' \
  --from-literal=smtp-password='your-smtp-password'
```

**Deploy:**
```bash
# Install with development values
helm install genascope-backend ./helm/genascope-backend -f ./helm/genascope-backend/values-dev.yaml

# Or with custom namespace
helm install genascope-backend ./helm/genascope-backend \
  -f ./helm/genascope-backend/values-dev.yaml \
  -n dev --create-namespace
```

### Staging Deployment

```bash
helm install genascope-backend ./helm/genascope-backend \
  -f ./helm/genascope-backend/values-staging.yaml \
  -n genascope-staging --create-namespace \
  --set secrets.databasePassword="your-staging-db-password" \
  --set secrets.openaiApiKey="your-openai-key"
```

### Production Deployment

```bash
helm install genascope-backend ./helm/genascope-backend \
  -f ./helm/genascope-backend/values-prod.yaml \
  -n genascope-prod --create-namespace \
  --set secrets.databasePassword="your-prod-db-password" \
  --set secrets.openaiApiKey="your-openai-key" \
  --set secrets.secretKey="your-secret-key"
```

## Configuration

### Environment-Specific Values

| File | Environment | Description |
|------|-------------|-------------|
| `values.yaml` | Base | Default configuration values |
| `values-dev.yaml` | Development | Local development with built-in PostgreSQL/Redis |
| `values-staging.yaml` | Staging | Pre-production environment with external services |
| `values-prod.yaml` | Production | Production-ready with high availability and security |

### Key Configuration Parameters

#### Application Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `app.environment` | Application environment | `dev` |
| `app.frontendUrl` | Frontend application URL | `http://localhost:3000` |
| `app.cors.origins` | Allowed CORS origins | `["http://localhost:3000"]` |

#### Database Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `app.database.external` | Use external database | `false` |
| `app.database.host` | Database host | `postgresql` |
| `app.database.port` | Database port | `5432` |
| `app.database.name` | Database name | `genascope` |
| `app.database.user` | Database user | `genascope` |

#### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.requests.cpu` | CPU request | `500m` |
| `resources.requests.memory` | Memory request | `1Gi` |
| `resources.limits.cpu` | CPU limit | `1000m` |
| `resources.limits.memory` | Memory limit | `2Gi` |

#### Autoscaling

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable HPA | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `1` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | CPU target | `80` |

## Secrets Management

The chart supports multiple approaches for managing secrets:

### Option 1: Sealed Secrets (Recommended for GitOps)

Sealed Secrets allow you to encrypt secrets and store them safely in Git repositories. This is the recommended approach for GitOps workflows.

See [SEALED_SECRETS.md](./SEALED_SECRETS.md) for detailed implementation guide.

Quick start:
```bash
# Generate encrypted secrets interactively
./scripts/generate-sealed-secrets.sh --namespace development --interactive

# Deploy with sealed secrets
./scripts/deploy-sealed-secrets.sh --namespace development
```

### Option 2: External Secrets (Current)

Use existing Kubernetes secrets created outside the chart:

```yaml
# values-dev.yaml (current approach)
app:
  database:
    passwordSecret:
      name: "pgvector-secret"
      key: "postgres-password"
  apis:
    openai:
      secretName: "openai-secret"
      secretKey: "api-key"
```

### Option 3: Direct Secret Creation

For development or CI/CD environments, you can create secrets directly:

```yaml
secrets:
  databasePassword: "your-database-password"
  secretKey: "your-secret-key"
  openaiApiKey: "your-openai-api-key"
  labApiKey: "your-lab-api-key"        # Optional
  smtpPassword: "your-smtp-password"   # Optional
```

### Setting Secrets via Command Line

```bash
helm install genascope-backend ./helm/genascope-backend \
  --set secrets.databasePassword="$(echo -n 'your-password' | base64)" \
  --set secrets.openaiApiKey="$(echo -n 'your-api-key' | base64)"
```

### Using External Secret Management

For production environments, consider using:
- [Sealed Secrets](https://sealed-secrets.netlify.app/)
- [External Secrets Operator](https://external-secrets.io/)
- [HashiCorp Vault](https://www.vaultproject.io/)

## Ingress Configuration

### Development (No TLS)

```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: api-dev.genascope.local
      paths:
        - path: /
          pathType: Prefix
```

### Production (With TLS)

```yaml
ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: api.genascope.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: genascope-backend-tls
      hosts:
        - api.genascope.com
```

## Database Setup

### Development (Built-in PostgreSQL)

```yaml
postgresql:
  enabled: true
  auth:
    database: "genascope_dev"
    username: "genascope"
    password: "dev-password"
```

### Production (External Database)

```yaml
app:
  database:
    external: true
    host: "your-db-host.com"
    port: 5432
    name: "genascope_prod"
    user: "genascope_prod"
postgresql:
  enabled: false
```

## Monitoring and Health Checks

The chart includes comprehensive health checks:

### Liveness Probe
- Endpoint: `/health`
- Initial delay: 30s (60s in production)
- Period: 10s (30s in production)

### Readiness Probe
- Endpoint: `/health`
- Initial delay: 5s (30s in production)
- Period: 5s (10s in production)

### Metrics
Add these annotations for Prometheus scraping:
```yaml
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

## Upgrading

```bash
# Upgrade with new values
helm upgrade genascope-backend ./helm/genascope-backend \
  -f ./helm/genascope-backend/values-prod.yaml

# Upgrade with new image tag
helm upgrade genascope-backend ./helm/genascope-backend \
  --set image.tag="v1.2.0"
```

## Backup and Recovery

### Database Backups
For external databases, ensure your database provider handles backups.

For built-in PostgreSQL (development only):
```bash
kubectl exec -it deployment/genascope-backend-postgresql \
  -- pg_dump -U genascope genascope_dev > backup.sql
```

### Application Data
Configure persistent volumes for any application data:
```yaml
persistence:
  enabled: true
  size: 10Gi
  storageClass: "gp2"
```

## Troubleshooting

### Common Issues

1. **Pod not starting**
   ```bash
   kubectl describe pod -l app.kubernetes.io/name=genascope-backend
   kubectl logs -l app.kubernetes.io/name=genascope-backend
   ```

2. **Database connection issues**
   ```bash
   kubectl exec -it deployment/genascope-backend -- env | grep DATABASE
   ```

3. **Ingress not working**
   ```bash
   kubectl get ingress
   kubectl describe ingress genascope-backend
   ```

### Health Check
```bash
# Port forward to test locally
kubectl port-forward svc/genascope-backend 8080:80

# Test health endpoint
curl http://localhost:8080/health
```

## Security Considerations

1. **Always use TLS in production**
2. **Rotate secrets regularly**
3. **Use external secret management**
4. **Review resource limits**
5. **Enable network policies**
6. **Use read-only root filesystem where possible**

## Contributing

1. Make changes to the Helm chart
2. Test with all three environments
3. Update this README if needed
4. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/martialbb/genascope-backend/issues
- Documentation: https://github.com/martialbb/genascope-backend/docs
