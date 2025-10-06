# Docker Deployment Example

This guide covers deploying NexusRAG with Docker Compose, including environment configuration, scaling, monitoring, and production hardening.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/nexus-rag.git
cd nexus-rag

# Create environment file
cp .env.example .env
# Edit .env with your OPENAI_API_KEY and other settings

# Start all services
docker compose up -d

# Verify
docker compose ps
curl http://localhost:5000/ready
curl http://localhost:3456/ping
```

---

## Service Architecture in Docker

```
docker compose up -d
  |
  +-- mongo          (MongoDB 7, port 27017, volume: mongo-data)
  +-- gateway        (FastAPI, port 5000, volume: vectorstore-data)
  +-- data-api       (Express, port 3456)
  +-- ui             (React/Nginx, port 3000)
  +-- redis          (Redis 7, port 6379, optional)
```

---

## Environment Configuration

### Minimal .env

```bash
OPENAI_API_KEY=sk-your-key-here
MONGO_URI=mongodb://mongo:27017
```

### Full Production .env

```bash
# --- Core ---
ENV=production
LOG_LEVEL=info

# --- MongoDB ---
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=nexusrag
MONGO_POOL_SIZE=20

# --- Gateway ---
GATEWAY_PORT=5000
GATEWAY_WORKERS=4
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
LLM_TEMPERATURE=0.5
LLM_MAX_TOKENS=2048
LLM_STREAMING=true
DEFAULT_SEARCH_MODE=combined
RETRIEVAL_TOP_K=10
RERANKING_ENABLED=true
RERANKER_TOP_K=5
AGENTIC_MODE=true
AGENT_MAX_ITERATIONS=5
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_RPM=120
REQUEST_TIMEOUT=120

# --- Cache ---
REDIS_URL=redis://redis:6379/0
CACHE_ENABLED=true
CACHE_TTL=3600

# --- Data API ---
DATA_API_PORT=3456
API_KEY=generate-a-secure-key-here
NODE_ENV=production

# --- UI (build-time) ---
VITE_GATEWAY_URL=http://localhost:5000
VITE_GATEWAY_WS_URL=ws://localhost:5000
VITE_DATA_API_URL=http://localhost:3456
```

---

## Customizing docker-compose.yml

### Adding Redis for Distributed Rate Limiting and Caching

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

volumes:
  redis-data:
```

### Adding a Reverse Proxy

For production, place NGINX in front of all services:

```yaml
services:
  nginx:
    image: nginx:1.25-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - gateway
      - data-api
      - ui
```

Example `nginx.conf`:

```nginx
events { worker_connections 1024; }

http {
    upstream gateway {
        server gateway:5000;
    }

    upstream data_api {
        server data-api:3456;
    }

    upstream ui {
        server ui:3000;
    }

    server {
        listen 80;
        server_name nexusrag.example.com;

        # Redirect to HTTPS in production
        # return 301 https://$host$request_uri;

        location /api/ {
            proxy_pass http://gateway;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_read_timeout 120s;
        }

        location /ws/ {
            proxy_pass http://gateway;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 86400s;
        }

        location /data/ {
            rewrite ^/data/(.*) /$1 break;
            proxy_pass http://data_api;
        }

        location / {
            proxy_pass http://ui;
        }
    }
}
```

---

## Scaling

### Horizontal Scaling of the Gateway

```bash
docker compose up -d --scale gateway=3
```

When scaling, the NGINX reverse proxy load-balances across all Gateway replicas. Ensure `REDIS_URL` is set so rate limiting and caching are shared across replicas.

### Scaling the Data API

```bash
docker compose up -d --scale data-api=2
```

The Data API is lightweight and typically needs fewer replicas than the Gateway.

### Resource Limits

Set resource limits in `docker-compose.yml` to prevent any single service from consuming all host resources:

```yaml
services:
  gateway:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 4G
        reservations:
          cpus: "0.5"
          memory: 1G

  data-api:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 1G

  ui:
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 256M

  mongo:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 4G
```

---

## Monitoring

### Container Health

```bash
# Check all container statuses
docker compose ps

# View resource usage
docker stats --no-stream

# Check Gateway readiness
curl -s http://localhost:5000/health | python3 -m json.tool
```

### Log Collection

```bash
# Follow all logs
docker compose logs -f

# Follow a specific service
docker compose logs -f gateway

# Export logs to a file
docker compose logs --no-color > nexusrag-logs.txt
```

For production, configure the Docker logging driver to ship logs to a centralized system:

```yaml
services:
  gateway:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
```

Or use Fluentd, Loki, or another log aggregation driver.

### Health Check Configuration

```yaml
services:
  gateway:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/alive"]
      interval: 15s
      timeout: 5s
      retries: 3
      start_period: 20s

  data-api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3456/ping"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s
```

---

## Production Tips

### 1. Use Named Volumes

Always use named volumes for persistent data to survive `docker compose down`:

```yaml
volumes:
  mongo-data:
  vectorstore-data:
  redis-data:
```

### 2. Pin Image Tags

Never use `latest` in production. Pin to a specific version:

```yaml
services:
  gateway:
    image: ghcr.io/nexusrag/gateway:1.2.3
```

### 3. Set Restart Policies

```yaml
services:
  gateway:
    restart: unless-stopped
  data-api:
    restart: unless-stopped
  mongo:
    restart: unless-stopped
```

### 4. Separate Build and Run

Build images in CI and push to a registry. Do not build on production hosts:

```bash
# In CI
docker compose build
docker compose push

# On production host
docker compose pull
docker compose up -d
```

### 5. Backup Before Upgrades

```bash
# Backup MongoDB
docker compose exec mongo mongodump --out /data/backup/$(date +%Y%m%d)

# Backup vector store
docker compose exec gateway tar czf /tmp/vs-backup.tar.gz /app/data/vectorstore
docker compose cp gateway:/tmp/vs-backup.tar.gz ./backups/
```

### 6. Secure MongoDB

If MongoDB is exposed to the network, enable authentication:

```yaml
services:
  mongo:
    image: mongo:7
    command: mongod --auth
    environment:
      MONGO_INITDB_ROOT_USERNAME: admin
      MONGO_INITDB_ROOT_PASSWORD: secure-password
```

Update `MONGO_URI` to include credentials:

```bash
MONGO_URI=mongodb://admin:<password>@mongo:27017
```

### 7. Enable TLS

For production with a domain name, use the NGINX reverse proxy with TLS certificates. See `docs/deployment.md` for cert-manager integration.

---

## Troubleshooting

See `docs/troubleshooting.md` for a comprehensive list of common issues and solutions.

Quick diagnostics:

```bash
docker compose ps                              # Service status
docker compose logs --tail=50 gateway          # Recent Gateway logs
curl -s http://localhost:5000/health           # Component health
docker compose exec mongo mongosh --eval "db.adminCommand('ping')"  # MongoDB check
```
