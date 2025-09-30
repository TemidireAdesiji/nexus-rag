# NexusRAG Troubleshooting Guide

This document covers the most common issues encountered when running NexusRAG, along with their root causes and solutions.

---

## 1. Gateway Fails to Start -- "OPENAI_API_KEY is required"

**Symptoms:** The Gateway exits immediately on startup with a configuration validation error.

**Cause:** The `OPENAI_API_KEY` environment variable is not set and `LLM_PROVIDER` is set to `openai` (the default).

**Solution:**

```bash
# Set the variable in your .env file
echo 'OPENAI_API_KEY=sk-your-key-here' >> .env

# Or pass it directly
OPENAI_API_KEY=sk-your-key docker compose up gateway
```

If you are using a local LLM endpoint, set `LLM_PROVIDER=local` and `OPENAI_BASE_URL` to your local server URL instead.

---

## 2. Gateway Fails to Start -- "Vector store path not found"

**Symptoms:** The Gateway logs `FileNotFoundError` referencing the vector store path.

**Cause:** The directory specified by `VECTOR_STORE_PATH` does not exist, or the container lacks write permissions.

**Solution:**

```bash
# Create the directory
mkdir -p ./data/vectorstore

# For Docker, ensure the volume mount exists
docker compose exec gateway ls -la /app/data/vectorstore

# Fix permissions if needed
chmod 755 ./data/vectorstore
```

In Kubernetes, verify the PersistentVolumeClaim is bound:

```bash
kubectl get pvc -n nexusrag
```

---

## 3. MongoDB Connection Refused

**Symptoms:** Gateway or Data API logs `ServerSelectionTimeoutError` or `MongoNetworkError`.

**Cause:** MongoDB is not running, the URI is incorrect, or network policies block the connection.

**Solution:**

```bash
# Check MongoDB is running
docker compose ps mongo
docker compose logs mongo

# Test connectivity from the Gateway container
docker compose exec gateway python -c "
from pymongo import MongoClient
c = MongoClient('mongodb://mongo:27017', serverSelectionTimeoutMS=5000)
print(c.server_info())
"

# Common fixes:
# - Use 'mongo' (service name) instead of 'localhost' in Docker Compose
# - Check MONGO_URI matches the actual host/port
# - For Atlas, ensure your IP is in the access list
```

---

## 4. CORS Errors in the Browser

**Symptoms:** The browser console shows `Access-Control-Allow-Origin` errors when the UI calls the Gateway.

**Cause:** The `CORS_ORIGINS` variable on the Gateway does not include the UI origin.

**Solution:**

```bash
# Set CORS_ORIGINS to match the UI URL exactly
CORS_ORIGINS=http://localhost:3000

# For multiple origins, use a comma-separated list
CORS_ORIGINS=http://localhost:3000,https://nexusrag.example.com
```

Restart the Gateway after changing this value. Do not use `*` in production.

---

## 5. WebSocket Connection Drops Immediately

**Symptoms:** The UI shows "Connection lost" shortly after connecting. The browser console shows a WebSocket close event with code 1006.

**Cause:** A reverse proxy or load balancer is terminating the WebSocket connection because it does not support or is not configured for WebSocket upgrades.

**Solution:**

For NGINX:

```nginx
location /ws/ {
    proxy_pass http://gateway:5000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 86400;
}
```

For Kubernetes NGINX Ingress, add annotations:

```yaml
annotations:
  nginx.ingress.kubernetes.io/websocket-services: "gateway"
  nginx.ingress.kubernetes.io/proxy-read-timeout: "86400"
  nginx.ingress.kubernetes.io/proxy-send-timeout: "86400"
```

For AWS ALB, ensure the target group protocol is HTTP (not HTTPS) and idle timeout is set to at least 300 seconds.

---

## 6. WebSocket Messages Arrive but No Tokens Stream

**Symptoms:** The WebSocket connects successfully and sends a `chat` message, but no `token` events are received. The `done` event eventually arrives with a complete answer.

**Cause:** `LLM_STREAMING` is set to `false`, so the Gateway waits for the full LLM response before sending it as a single message.

**Solution:**

```bash
LLM_STREAMING=true
```

Restart the Gateway.

---

## 7. Rate Limiting Triggers Unexpectedly (429 Responses)

**Symptoms:** Clients receive HTTP 429 responses despite low traffic volume.

**Cause:** In multi-replica deployments without Redis, each Gateway instance maintains its own in-memory rate limit state. If a load balancer distributes requests across replicas, each replica sees a fraction of the traffic but the client may still hit limits on a single replica due to sticky sessions or uneven distribution.

**Solution:**

Enable distributed rate limiting with Redis:

```bash
REDIS_URL=redis://redis:6379/0
```

This ensures all replicas share a single rate limit counter per client IP.

---

## 8. Retrieval Returns Empty Results

**Symptoms:** The `sources` array in the response is empty even though documents have been ingested.

**Cause (A):** The vector store is empty or pointing to a different path than where ingestion wrote.

**Cause (B):** The embedding model used for queries differs from the one used during ingestion.

**Solution:**

```bash
# Verify the vector store has data
curl http://localhost:5000/api/platform/info
# Check the vector_store field and document count

# Ensure EMBEDDING_MODEL and VECTOR_STORE_PATH match
# between ingestion and query time

# Re-ingest if the embedding model was changed
curl -X POST http://localhost:5000/api/ingest \
  -F "file=@document.pdf"
```

---

## 9. Reranker Out-of-Memory (OOM) Errors

**Symptoms:** The Gateway process is killed by the OOM killer during reranking, or logs show `torch.cuda.OutOfMemoryError`.

**Cause:** The cross-encoder reranker model is too large for the available memory, especially when `RETRIEVAL_TOP_K` is high and multiple requests rerank concurrently.

**Solution:**

```bash
# Option 1: Reduce the number of candidates sent to the reranker
RETRIEVAL_TOP_K=10   # down from a higher value
RERANKER_TOP_K=3     # fewer final results

# Option 2: Use a smaller reranker model
RERANKER_MODEL=cross-encoder/ms-marco-MiniLM-L-4-v2

# Option 3: Run on CPU with limited threads (slower but bounded memory)
RERANKER_DEVICE=cpu

# Option 4: Increase container memory limits
# In K8s: set resources.limits.memory to 8Gi
```

---

## 10. Docker Build Fails -- "No space left on device"

**Symptoms:** `docker build` or `docker compose build` fails with `ENOSPC`.

**Cause:** Docker build cache and old images have consumed all disk space.

**Solution:**

```bash
# Remove unused images and build cache
docker system prune -af
docker builder prune -af

# Check disk usage
docker system df

# For recurring issues, configure Docker daemon with a build cache limit
# /etc/docker/daemon.json:
# { "builder": { "gc": { "defaultKeepStorage": "10GB" } } }
```

---

## 11. Data API Returns 401 on All Requests

**Symptoms:** Every request to `/api/*` endpoints returns `{"error": {"code": "unauthorized"}}`.

**Cause:** The `API_KEY` variable is set on the Data API, requiring all requests to include a matching `Authorization: Bearer <key>` header.

**Solution:**

```bash
# Include the header in your requests
curl -H "Authorization: Bearer your-data-api-key" \
  http://localhost:3456/api/personnel

# Or obtain a credential first
curl http://localhost:3456/auth/credential
# Use the returned api_key in subsequent requests
```

---

## 12. UI Shows Blank Page After Build

**Symptoms:** Navigating to `http://localhost:3000` shows a white screen. The browser console shows errors about failed API calls.

**Cause:** The `VITE_GATEWAY_URL` and `VITE_DATA_API_URL` variables were not set at build time. Vite inlines these at build, not at runtime.

**Solution:**

```bash
# Rebuild the UI with correct variables
VITE_GATEWAY_URL=http://localhost:5000 \
VITE_DATA_API_URL=http://localhost:3456 \
npm run build

# For Docker, pass as build args
docker compose build --build-arg VITE_GATEWAY_URL=http://localhost:5000 ui
```

---

## 13. Kubernetes Pods Stuck in CrashLoopBackOff

**Symptoms:** Pods restart repeatedly. `kubectl describe pod` shows the liveness probe failing.

**Cause:** The service takes longer to start than the `initialDelaySeconds` allows, or a required dependency (MongoDB, Redis) is unreachable.

**Solution:**

```bash
# Check pod logs
kubectl logs -n nexusrag <pod-name> --previous

# Increase probe delay if startup is slow
# livenessProbe.initialDelaySeconds: 30  (up from 10)

# Verify dependencies
kubectl exec -n nexusrag <pod-name> -- python -c "
import urllib.request
urllib.request.urlopen('http://data-api:3456/ping')
print('Data API reachable')
"

# Check secrets are mounted
kubectl exec -n nexusrag <pod-name> -- env | grep OPENAI
```

---

## 14. Slow Query Performance (> 10 seconds)

**Symptoms:** Queries take more than 10 seconds to return, especially with the `expanded` or `decomposed` strategies.

**Cause:** These strategies make multiple LLM calls (for query expansion or decomposition) before retrieval, adding latency.

**Solution:**

```bash
# Use a faster strategy for latency-sensitive use cases
# strategy: "vector" or "combined"

# Reduce expansion count
QUERY_EXPANSION_COUNT=2   # down from 3

# Enable caching to avoid re-embedding repeated queries
CACHE_ENABLED=true
REDIS_URL=redis://redis:6379/0

# Use a faster LLM model for expansion/decomposition
OPENAI_MODEL=gpt-4o-mini
```

---

## 15. Ingestion Fails for Large Documents

**Symptoms:** `POST /api/ingest` returns a 413 or times out for large PDF files.

**Cause:** The document exceeds the maximum upload size or the request timeout.

**Solution:**

```bash
# Increase request timeout (Gateway)
REQUEST_TIMEOUT=300

# For Docker/NGINX, also increase proxy limits
# nginx.conf:
# client_max_body_size 100m;
# proxy_read_timeout 300;

# Split very large documents before ingestion
# The Gateway processes documents sequentially; files over 50MB
# should be split into smaller parts
```

---

## Diagnostic Commands

Quick reference for gathering diagnostic information:

```bash
# Service health
curl -s http://localhost:5000/health | python -m json.tool
curl -s http://localhost:3456/ping

# Gateway configuration
curl -s http://localhost:5000/api/platform/info | python -m json.tool

# Docker logs
docker compose logs --tail=100 gateway
docker compose logs --tail=100 data-api

# Kubernetes diagnostics
kubectl get pods -n nexusrag
kubectl describe pod -n nexusrag <pod-name>
kubectl logs -n nexusrag <pod-name> --tail=200
kubectl top pods -n nexusrag

# MongoDB connectivity
mongosh "$MONGO_URI" --eval "db.adminCommand('ping')"

# Vector store size
du -sh ./data/vectorstore/
```
