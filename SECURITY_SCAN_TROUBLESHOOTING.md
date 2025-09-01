# Security Scan Upload Issue - Troubleshooting Guide

## Current Issue
The security scan is working correctly and Trivy successfully generates SARIF results, but uploading to GitHub's Security tab fails with:
```
Resource not accessible by integration - https://docs.github.com/rest/actions/workflow-runs#get-a-workflow-run
```

## Root Cause Analysis

This error typically occurs due to one of these reasons:

### 1. GitHub Advanced Security Not Enabled (Most Likely)
For **private repositories**, GitHub's Security tab and Code Scanning features require **GitHub Advanced Security** to be enabled.

**Check if this is the issue:**
1. Go to your repository on GitHub
2. Click on the "Security" tab
3. If you see a message about enabling GitHub Advanced Security, that's the issue

**Solutions:**
- **Option A**: Enable GitHub Advanced Security (requires paid plan)
- **Option B**: Make the repository public (free)
- **Option C**: Use workflow artifacts instead (current fallback)

### 2. Insufficient Repository Permissions
The GitHub token might need additional permissions.

**What we've tried:**
- ✅ Added `actions: read` permission
- ✅ Added `contents: read` permission  
- ✅ Added `packages: read` permission
- ✅ Added `security-events: write` permission

### 3. Organization-level Restrictions
If this is an organization repository, Advanced Security might be disabled at the org level.

## Current Workarounds Implemented

### 1. Fallback Artifact Upload ✅
```yaml
- name: Upload SARIF as workflow artifact (fallback)
  uses: actions/upload-artifact@v3
  if: always()
  with:
    name: trivy-sarif-results
    path: trivy-results.sarif
    retention-days: 30
```

**How to access:** Go to the workflow run → "Artifacts" section → Download "trivy-sarif-results"

### 2. Continue on Error ✅
The security scan won't fail the entire workflow:
```yaml
continue-on-error: true
```

### 3. Scan Summary ✅
Displays basic information about found vulnerabilities in the workflow logs.

## Accessing Security Scan Results

Since the Security tab upload might fail, here are alternative ways to access results:

### Method 1: Workflow Artifacts
1. Go to Actions → Latest workflow run
2. Scroll to "Artifacts" section
3. Download "trivy-sarif-results"
4. Open the SARIF file with any text editor or SARIF viewer

### Method 2: Manual Local Scan
```bash
# Install Trivy locally
brew install trivy

# Pull and scan the image
docker pull ghcr.io/martialbb/genascope-backend:latest
trivy image ghcr.io/martialbb/genascope-backend:latest

# Generate SARIF for tools that support it
trivy image --format sarif --output local-scan.sarif ghcr.io/martialbb/genascope-backend:latest
```

### Method 3: VS Code SARIF Viewer
1. Install "SARIF Viewer" extension in VS Code
2. Download the SARIF artifact from workflow
3. Open the .sarif file in VS Code

## Enabling GitHub Advanced Security

If you want the full Security tab integration:

### For Personal Repositories
1. Go to repository Settings
2. Scroll to "Security & analysis"
3. Enable "Dependency graph" (free)
4. Enable "Dependabot alerts" (free)
5. Enable "Code scanning" (requires Advanced Security for private repos)

### For Organization Repositories
1. Organization Settings → "Security & analysis"
2. Enable Advanced Security for the organization
3. Enable it for specific repositories

**Note:** GitHub Advanced Security requires a paid GitHub plan for private repositories.

## Alternative: Make Repository Public

If you don't need the repository to be private:
1. Go to repository Settings
2. Scroll to "Danger Zone"
3. Click "Change repository visibility"
4. Select "Make public"

**Benefits:**
- ✅ Full Security tab access
- ✅ Code scanning alerts
- ✅ Dependency graph
- ✅ No additional costs

**Considerations:**
- ❌ Code becomes publicly visible
- ❌ May not be suitable for proprietary projects

## What's Working Now

✅ **Security scanning is functional** - Trivy successfully scans the Docker image
✅ **Vulnerability detection** - Scans OS packages and Python dependencies  
✅ **SARIF generation** - Results are properly formatted
✅ **Workflow artifacts** - Results available for download
✅ **Non-blocking** - Scan failures don't prevent deployment

## Recommended Next Steps

1. **Short-term**: Use workflow artifacts to access scan results
2. **Medium-term**: Consider enabling GitHub Advanced Security if budget allows
3. **Long-term**: Evaluate if repository should be public for open-source benefits

## Monitoring Security

Even without Security tab integration, you can:
- Review SARIF artifacts after each build
- Set up notifications for workflow failures
- Run manual scans during development
- Use external security tools that integrate with CI/CD

The security scanning is working correctly - it's just the GitHub integration that requires additional permissions/features.
