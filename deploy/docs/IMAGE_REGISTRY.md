# Docker Image Registry Procedures

This document describes how to build, tag, and push NexusRAG Docker images to the GitHub Container Registry (GHCR).

---

## Prerequisites

- Docker 24+ with Buildx enabled
- A GitHub personal access token (PAT) with `write:packages` scope
- Repository write access to the NexusRAG GitHub organization

---

## Authentication

Log in to GHCR before pushing images:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_USERNAME" --password-stdin
```

In CI (GitHub Actions), use the built-in `GITHUB_TOKEN`:

```yaml
- name: Log in to GHCR
  uses: docker/login-action@v3
  with:
    registry: ghcr.io
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}
```

---

## Image Naming Convention

All images are published under the organization namespace:

```
ghcr.io/nexusrag/gateway:<tag>
ghcr.io/nexusrag/data-api:<tag>
ghcr.io/nexusrag/ui:<tag>
```

### Tagging Strategy

| Tag Pattern | When Applied | Example |
|-------------|-------------|---------|
| `latest` | Every push to `main` | `ghcr.io/nexusrag/gateway:latest` |
| `<semver>` | Release tags | `ghcr.io/nexusrag/gateway:1.2.3` |
| `<semver>-rc.<n>` | Release candidates | `ghcr.io/nexusrag/gateway:1.2.3-rc.1` |
| `sha-<short>` | Every commit build | `ghcr.io/nexusrag/gateway:sha-abc1234` |
| `pr-<number>` | Pull request builds | `ghcr.io/nexusrag/gateway:pr-42` |

---

## Building Images Locally

### Single-Architecture Build

```bash
# Gateway
docker build -t ghcr.io/nexusrag/gateway:dev \
  -f services/gateway/Dockerfile \
  services/gateway/

# Data API
docker build -t ghcr.io/nexusrag/data-api:dev \
  -f services/data-api/Dockerfile \
  services/data-api/

# UI
docker build -t ghcr.io/nexusrag/ui:dev \
  -f services/ui/Dockerfile \
  services/ui/
```

### Multi-Architecture Build (amd64 + arm64)

```bash
# Create a builder instance (one-time)
docker buildx create --name nexusrag-builder --use

# Build and push multi-arch images
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/nexusrag/gateway:1.2.3 \
  -t ghcr.io/nexusrag/gateway:latest \
  -f services/gateway/Dockerfile \
  --push \
  services/gateway/

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/nexusrag/data-api:1.2.3 \
  -t ghcr.io/nexusrag/data-api:latest \
  -f services/data-api/Dockerfile \
  --push \
  services/data-api/

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t ghcr.io/nexusrag/ui:1.2.3 \
  -t ghcr.io/nexusrag/ui:latest \
  -f services/ui/Dockerfile \
  --push \
  services/ui/
```

---

## CI/CD Pipeline (GitHub Actions)

The following workflow builds and pushes images on every push to `main` and on release tags:

```yaml
name: Build and Push Images

on:
  push:
    branches: [main]
    tags: ["v*"]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  GATEWAY_IMAGE: ghcr.io/nexusrag/gateway
  DATA_API_IMAGE: ghcr.io/nexusrag/data-api
  UI_IMAGE: ghcr.io/nexusrag/ui

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    strategy:
      matrix:
        service:
          - name: gateway
            context: services/gateway
            image: ghcr.io/nexusrag/gateway
          - name: data-api
            context: services/data-api
            image: ghcr.io/nexusrag/data-api
          - name: ui
            context: services/ui
            image: ghcr.io/nexusrag/ui

    steps:
      - uses: actions/checkout@v4

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ matrix.service.image }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha,prefix=sha-

      - uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.service.context }}
          platforms: linux/amd64,linux/arm64
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

---

## Image Verification

After pushing, verify images are available:

```bash
# List tags for a service
docker manifest inspect ghcr.io/nexusrag/gateway:1.2.3

# Pull and test locally
docker pull ghcr.io/nexusrag/gateway:1.2.3
docker run --rm ghcr.io/nexusrag/gateway:1.2.3 python -c "print('OK')"
```

---

## Image Cleanup

Remove old images from GHCR to manage storage costs. Use the GitHub API or the `ghcr-cleanup-action`:

```yaml
- uses: actions/delete-package-versions@v5
  with:
    package-name: gateway
    package-type: container
    min-versions-to-keep: 10
    delete-only-untagged-versions: true
```

---

## Security Scanning

All images are scanned for vulnerabilities using Trivy in CI:

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: ${{ matrix.service.image }}:${{ steps.meta.outputs.version }}
    format: sarif
    output: trivy-results.sarif

- name: Upload scan results
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: trivy-results.sarif
```

Images with critical vulnerabilities must not be promoted to production. See `deploy/docs/RELEASE_CHECKLIST.md` for the full gate criteria.
