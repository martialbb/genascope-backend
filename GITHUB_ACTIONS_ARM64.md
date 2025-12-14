# GitHub Actions Build Performance - ARM64 Issue

## Problem
GitHub Actions builds taking 50+ minutes (sometimes up to 60+ minutes)

## Root Cause
The workflow was building **both AMD64 and ARM64** architectures:
```yaml
platforms=linux/amd64,linux/arm64  # Building both!
timeout=45m                         # Long timeout needed
```

### Why ARM64 is Slow on GitHub Actions
- GitHub Actions runners are **AMD64 architecture**
- To build ARM64 images, it uses **QEMU emulation**
- Emulation is 10-50x slower than native builds
- Installing large Python packages (pandas, numpy, langchain, etc.) under emulation is extremely slow

### Typical Build Times
- **AMD64 only**: 10-15 minutes
- **AMD64 + ARM64**: 30-60+ minutes
- **ARM64 emulated build alone**: 20-45 minutes

## Solution Implemented

Changed GitHub Actions to build **AMD64 only**:

```yaml
# Before
platforms=linux/amd64,linux/arm64  # Slow!
timeout=45m

# After  
platforms=linux/amd64              # Fast!
timeout=20m
```

### Benefits
✅ **Faster CI/CD**: 10-15 minutes instead of 45-60 minutes  
✅ **Reduced GitHub Actions minutes**: Save ~70% of build time  
✅ **Faster feedback loop**: Quicker deployments and testing  
✅ **Cost savings**: Less compute time = lower costs

### ARM64 Support Maintained
- Local builds on M1/M2 Macs use `Dockerfile.arm64`
- Manual ARM64 workflow available: `.github/workflows/build-arm64.yml`
- Can trigger manual ARM64 builds when needed

## When to Use ARM64 Builds

### Use AMD64 (Default) for:
- ✅ Production cloud deployments (AWS, GCP, Azure mostly use AMD64)
- ✅ CI/CD pipelines
- ✅ Fast iteration and testing
- ✅ Kubernetes clusters (most run AMD64)

### Use ARM64 for:
- Mac M1/M2 local development
- AWS Graviton instances (if using ARM-based cloud)
- Raspberry Pi deployments
- Cost optimization in ARM-based cloud infrastructure

## Build Time Comparison

| Configuration | Build Time | Use Case |
|--------------|------------|----------|
| AMD64 only | 10-15 min | ✅ **Default** - Fast CI/CD |
| ARM64 only (emulated) | 20-45 min | Local M1/M2 dev |
| AMD64 + ARM64 | 30-60 min | Multi-arch releases |
| ARM64 (native on M1) | 60-90 sec | **Fastest** - Local dev |

## How to Build ARM64 When Needed

### Option 1: Local Build (Fastest on M1/M2)
```bash
./build.sh --dev  # Uses Dockerfile.arm64, takes ~60 seconds
```

### Option 2: Manual GitHub Workflow
1. Go to Actions → Build ARM64 Docker Image (Manual)
2. Click "Run workflow"
3. Select "force_build: true"
4. Wait 30-45 minutes

### Option 3: Enable for Specific Releases
Manually edit workflow to build ARM64 for tagged releases only:
```yaml
if: startsWith(github.ref, 'refs/tags/v')
  platforms: linux/amd64,linux/arm64
```

## Current Status
- ✅ GitHub Actions: AMD64 only (~10-15 min builds)
- ✅ Local M1/M2: ARM64 via build.sh (~60 sec builds)
- ✅ Manual ARM64: Available via workflow_dispatch
- ✅ Deployment: Uses AMD64 images from GitHub Container Registry

---
**Last Updated**: October 9, 2025  
**Impact**: Reduced CI/CD time by 70%
