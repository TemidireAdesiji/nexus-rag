# Release Checklist

This checklist must be completed before any NexusRAG release is promoted to production. Each gate must pass; any failure blocks the release until resolved.

---

## Pre-Release Gates

### Code Quality

- [ ] All CI checks pass on the release branch (lint, type checking, unit tests)
- [ ] Code coverage meets the minimum threshold (80% for Gateway, 70% for Data API, 60% for UI)
- [ ] No new `ruff` or `eslint` warnings introduced
- [ ] All `TODO` and `FIXME` comments in changed files have been addressed or tracked in issues
- [ ] Dependency audit passes with no critical or high vulnerabilities (`pip audit`, `npm audit`)

### Testing

- [ ] All unit tests pass
- [ ] All integration tests pass against a staging environment
- [ ] Retrieval accuracy benchmarks show no regression (measured against the evaluation dataset)
- [ ] Load test completed: Gateway sustains 100 concurrent requests with p95 latency under 5 seconds
- [ ] WebSocket streaming tested with 50 concurrent connections
- [ ] OpenAI-compatible endpoint validated with the OpenAI Python SDK

### Security

- [ ] Docker images scanned with Trivy; no critical vulnerabilities
- [ ] No secrets committed to the repository (verified by `trufflehog` or `gitleaks`)
- [ ] CORS configuration reviewed; no wildcard origins in production
- [ ] Rate limiting verified; 429 responses returned at configured threshold
- [ ] API authentication validated; unauthenticated requests return 401

### Documentation

- [ ] CHANGELOG.md updated with all user-facing changes
- [ ] API reference updated for any new or modified endpoints
- [ ] Configuration reference updated for any new environment variables
- [ ] Migration guide written if the release includes breaking changes

### Infrastructure

- [ ] Docker images built and pushed to GHCR with the release tag
- [ ] Multi-architecture images verified (amd64 and arm64)
- [ ] Kubernetes manifests updated with the new image tag
- [ ] ConfigMap and Secret changes documented
- [ ] Database migration scripts tested (if applicable)
- [ ] Vector store compatibility verified (if embedding model changed)

### Deployment Readiness

- [ ] Staging deployment completed and validated
- [ ] Canary deployment plan prepared (see `deploy/docs/PROGRESSIVE_DELIVERY.md`)
- [ ] Rollback procedure tested
- [ ] Monitoring dashboards reviewed; all panels rendering data
- [ ] Alerting rules verified; test alerts fire correctly
- [ ] On-call engineer identified and briefed

---

## Release Process

1. **Create the release branch:**
   ```bash
   git checkout -b release/v1.2.3
   ```

2. **Bump version numbers:**
   - `services/gateway/pyproject.toml` -- `version = "1.2.3"`
   - `services/data-api/package.json` -- `"version": "1.2.3"`
   - `services/ui/package.json` -- `"version": "1.2.3"`

3. **Update CHANGELOG.md** with the release date and all changes.

4. **Open a pull request** from `release/v1.2.3` to `main`.

5. **Complete this checklist** by checking every box above.

6. **Merge the PR** after all gates pass and at least one reviewer approves.

7. **Tag the release:**
   ```bash
   git tag -a v1.2.3 -m "Release v1.2.3"
   git push origin v1.2.3
   ```

8. **CI builds and pushes images** with the `v1.2.3` tag.

9. **Deploy to staging** and validate.

10. **Deploy to production** using the progressive delivery strategy.

11. **Create a GitHub Release** with the changelog entry.

---

## Post-Release

- [ ] Production health verified (all probes green for 15 minutes)
- [ ] Smoke test completed (send a query, verify response)
- [ ] Monitoring dashboards show no anomalies
- [ ] Release announced in the team channel
- [ ] Release branch deleted
