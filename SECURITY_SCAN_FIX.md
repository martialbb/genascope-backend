# Security Scan Fix Documentation

## Issues Fixed

### 1. Authentication Error
**Problem**: Trivy security scanner was failing with `UNAUTHORIZED: authentication required` when trying to pull the Docker image from GitHub Container Registry (GHCR).

**Root Cause**: The security scan job lacked authentication credentials to access the private Docker image.

**Solution**:
- Added Docker registry login step before running Trivy
- Added `packages: read` permission to allow pulling images
- Configured authentication with `GITHUB_TOKEN`

### 2. Deprecated CodeQL Action
**Problem**: GitHub was showing deprecation warnings for CodeQL Action v2.

**Solution**: Updated from `github/codeql-action/upload-sarif@v2` to `@v3`

## Implementation Details

### Security Scan Job Configuration
```yaml
security-scan:
  needs: build-and-push
  runs-on: ubuntu-latest
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  permissions:
    contents: read      # Read repository content
    packages: read      # Pull Docker images from GHCR
    security-events: write  # Upload security scan results
  
  steps:
  - name: Log in to Container Registry
    uses: docker/login-action@v3
    with:
      registry: ${{ env.REGISTRY }}
      username: ${{ github.actor }}
      password: ${{ secrets.GITHUB_TOKEN }}

  - name: Run Trivy vulnerability scanner
    uses: aquasecurity/trivy-action@master
    with:
      image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
      format: 'sarif'
      output: 'trivy-results.sarif'
      timeout: '10m'
      exit-code: '0'  # Don't fail the workflow on vulnerabilities

  - name: Upload Trivy scan results to GitHub Security tab
    uses: github/codeql-action/upload-sarif@v3
    if: always()
    with:
      sarif_file: 'trivy-results.sarif'
```

## Security Scan Features

### Trivy Scanner
- **What it scans**: OS packages and application dependencies for known vulnerabilities
- **Output format**: SARIF (Static Analysis Results Interchange Format)
- **Integration**: Results appear in GitHub Security tab under "Code scanning alerts"
- **Frequency**: Runs on every push to main branch after successful build

### Configuration Options
- **Timeout**: 10 minutes to prevent hanging scans
- **Exit code**: Set to 0 to prevent workflow failure on vulnerabilities
- **Format**: SARIF for GitHub Security integration
- **Scope**: Full image scan including OS and library vulnerabilities

## Benefits

1. **Automated Security**: Every main branch deployment is automatically scanned for vulnerabilities
2. **GitHub Integration**: Results appear directly in GitHub's Security tab
3. **Non-blocking**: Vulnerabilities don't prevent deployment (configurable)
4. **Comprehensive**: Scans both OS packages and application dependencies
5. **Private Repository Support**: Works with private repositories using proper authentication

## Monitoring

- Check the "Security" tab in your GitHub repository
- Review Code scanning alerts for any detected vulnerabilities
- Monitor workflow runs for scan completion status
- Use GitHub's security advisories for vulnerability management

## Troubleshooting

### Common Issues
1. **Authentication errors**: Ensure `packages: read` permission is set
2. **Timeout errors**: Increase timeout value if needed
3. **SARIF upload failures**: Check if CodeQL action version is current

### Manual Security Scans
You can also run Trivy locally:
```bash
# Install Trivy
brew install trivy

# Scan local image
docker pull ghcr.io/martialbb/genascope-backend:latest
trivy image ghcr.io/martialbb/genascope-backend:latest

# Generate SARIF report
trivy image --format sarif --output trivy-results.sarif ghcr.io/martialbb/genascope-backend:latest
```

## Next Steps

1. Monitor the security scan results in GitHub Security tab
2. Set up notifications for new vulnerabilities
3. Consider adding security policies for vulnerability handling
4. Review and prioritize any detected vulnerabilities
