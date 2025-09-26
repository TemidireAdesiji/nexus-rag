# NexusRAG Configuration Reference

This document provides a complete reference for all configuration options across NexusRAG services. All configuration is managed through environment variables, which can be set directly, via `.env` files, Docker Compose environment blocks, or Kubernetes ConfigMaps and Secrets.

---

## Gateway Configuration (FastAPI -- port 5000)

### Core Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GATEWAY_HOST` | string | `0.0.0.0` | Bind address for the Gateway server |
| `GATEWAY_PORT` | integer | `5000` | Port the Gateway listens on |
| `GATEWAY_WORKERS` | integer | `1` | Number of Uvicorn worker processes |
| `LOG_LEVEL` | string | `info` | Logging level (`debug`, `info`, `warning`, `error`, `critical`) |
| `ENV` | string | `development` | Environment name (`development`, `staging`, `production`) |
| `DEBUG` | boolean | `false` | Enable debug mode with verbose logging and stack traces |
| `CORS_ORIGINS` | string | `*` | Comma-separated list of allowed CORS origins |
| `RATE_LIMIT_RPM` | integer | `60` | Maximum requests per minute per IP address |
| `RATE_LIMIT_BURST` | integer | `10` | Burst allowance above the per-minute rate |
| `REQUEST_TIMEOUT` | integer | `120` | Maximum request duration in seconds before timeout |

### MongoDB Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MONGO_URI` | string | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | string | `nexusrag` | Database name for Gateway collections |
| `MONGO_POOL_SIZE` | integer | `10` | Maximum connections in the Motor connection pool |
| `MONGO_TIMEOUT_MS` | integer | `5000` | Connection timeout in milliseconds |
| `MONGO_RETRY_WRITES` | boolean | `true` | Enable retryable writes |

### LLM Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_PROVIDER` | string | `openai` | LLM provider (`openai`, `azure`, `local`) |
| `OPENAI_API_KEY` | string | -- | OpenAI API key (required when provider is `openai`) |
| `OPENAI_MODEL` | string | `gpt-4o` | Model identifier for chat completions |
| `OPENAI_BASE_URL` | string | `https://api.openai.com/v1` | Base URL for OpenAI-compatible API |
| `AZURE_API_KEY` | string | -- | Azure OpenAI API key |
| `AZURE_ENDPOINT` | string | -- | Azure OpenAI endpoint URL |
| `AZURE_API_VERSION` | string | `2024-02-01` | Azure OpenAI API version |
| `AZURE_DEPLOYMENT` | string | -- | Azure deployment name |
| `LLM_TEMPERATURE` | float | `0.7` | Sampling temperature for generation |
| `LLM_MAX_TOKENS` | integer | `2048` | Maximum tokens in generated response |
| `LLM_STREAMING` | boolean | `true` | Enable streaming responses from the LLM |

### Embedding Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `EMBEDDING_MODEL` | string | `text-embedding-3-small` | Embedding model for vectorization |
| `EMBEDDING_DIMENSIONS` | integer | `1536` | Dimensionality of embedding vectors |
| `EMBEDDING_BATCH_SIZE` | integer | `100` | Number of texts to embed in a single API call |

### Vector Store Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VECTOR_STORE_TYPE` | string | `faiss` | Vector store backend (`faiss`, `chroma`, `qdrant`) |
| `VECTOR_STORE_PATH` | string | `./data/vectorstore` | Path for on-disk vector store files |
| `CHROMA_HOST` | string | `localhost` | Chroma server host (when using Chroma backend) |
| `CHROMA_PORT` | integer | `8000` | Chroma server port |
| `QDRANT_URL` | string | -- | Qdrant server URL (when using Qdrant backend) |
| `QDRANT_API_KEY` | string | -- | Qdrant API key |

### Retrieval Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEFAULT_SEARCH_MODE` | string | `vector` | Default retrieval strategy (`vector`, `combined`, `expanded`, `decomposed`) |
| `RETRIEVAL_TOP_K` | integer | `10` | Number of chunks to retrieve before reranking |
| `CHUNK_SIZE` | integer | `1000` | Character count per chunk during ingestion |
| `CHUNK_OVERLAP` | integer | `200` | Character overlap between consecutive chunks |
| `BM25_WEIGHT` | float | `0.3` | Weight for BM25 scores in the combined strategy (vector weight is `1 - BM25_WEIGHT`) |
| `QUERY_EXPANSION_COUNT` | integer | `3` | Number of expanded queries to generate in the expanded strategy |

### Reranking Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `RERANKING_ENABLED` | boolean | `true` | Enable cross-encoder reranking after retrieval |
| `RERANKER_MODEL` | string | `cross-encoder/ms-marco-MiniLM-L-6-v2` | HuggingFace model ID for reranking |
| `RERANKER_TOP_K` | integer | `5` | Number of chunks to keep after reranking |
| `RERANKER_DEVICE` | string | `cpu` | Device for reranker inference (`cpu`, `cuda`) |

### Agentic Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AGENTIC_MODE` | boolean | `false` | Enable the agentic orchestration layer |
| `AGENT_MAX_ITERATIONS` | integer | `5` | Maximum tool-call iterations per agent run |
| `AGENT_TOOLS` | string | `rag_search,data_api_lookup` | Comma-separated list of enabled agent tools |
| `DATA_API_URL` | string | `http://localhost:3456` | Internal URL of the Data API for agent tool calls |

### Redis / Cache Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REDIS_URL` | string | -- | Redis connection URL (enables distributed rate limiting and caching) |
| `CACHE_TTL` | integer | `3600` | Cache time-to-live in seconds |
| `CACHE_ENABLED` | boolean | `false` | Enable embedding and reranker result caching |

---

## Data API Configuration (Express -- port 3456)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATA_API_PORT` | integer | `3456` | Port the Data API listens on |
| `DATA_API_HOST` | string | `0.0.0.0` | Bind address |
| `MONGO_URI` | string | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGO_DB_NAME` | string | `nexusrag_data` | Database name for Data API collections |
| `API_KEY` | string | -- | API key for authenticating inbound requests |
| `CORS_ORIGINS` | string | `*` | Comma-separated allowed CORS origins |
| `LOG_LEVEL` | string | `info` | Logging level |
| `NODE_ENV` | string | `development` | Node environment |
| `CORPUS_STORAGE_PATH` | string | `./data/corpus` | Path for corpus archive files |
| `MAX_UPLOAD_SIZE` | string | `50mb` | Maximum upload payload size |

---

## UI Configuration (React/Vite -- port 3000)

UI configuration is set at build time via Vite environment variables (prefixed with `VITE_`).

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `VITE_GATEWAY_URL` | string | `http://localhost:5000` | Gateway API base URL |
| `VITE_GATEWAY_WS_URL` | string | `ws://localhost:5000` | Gateway WebSocket URL |
| `VITE_DATA_API_URL` | string | `http://localhost:3456` | Data API base URL |
| `VITE_APP_TITLE` | string | `NexusRAG` | Application title displayed in the header |
| `VITE_DEFAULT_STRATEGY` | string | `vector` | Default retrieval strategy in the UI |
| `VITE_ENABLE_SOURCE_VIEW` | boolean | `true` | Show source chunks in the chat interface |
| `VITE_MAX_MESSAGE_LENGTH` | integer | `4000` | Maximum characters per user message |

---

## Docker Compose Environment

When deploying with Docker Compose, environment variables are set in the `environment` block of each service or via an `.env` file in the project root. Docker Compose automatically reads a `.env` file if present.

### Example `.env` File

```bash
# --- MongoDB ---
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=nexusrag

# --- Gateway ---
GATEWAY_PORT=5000
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
LLM_TEMPERATURE=0.7
DEFAULT_SEARCH_MODE=combined
RERANKING_ENABLED=true
AGENTIC_MODE=false
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_RPM=120

# --- Data API ---
DATA_API_PORT=3456
API_KEY=your-data-api-key

# --- UI (build-time) ---
VITE_GATEWAY_URL=http://localhost:5000
VITE_GATEWAY_WS_URL=ws://localhost:5000
VITE_DATA_API_URL=http://localhost:3456
```

---

## Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nexusrag-config
  namespace: nexusrag
data:
  GATEWAY_PORT: "5000"
  GATEWAY_WORKERS: "4"
  LOG_LEVEL: "info"
  ENV: "production"
  MONGO_DB_NAME: "nexusrag"
  DEFAULT_SEARCH_MODE: "combined"
  RERANKING_ENABLED: "true"
  RETRIEVAL_TOP_K: "10"
  RERANKER_TOP_K: "5"
  LLM_TEMPERATURE: "0.5"
  LLM_MAX_TOKENS: "2048"
  AGENTIC_MODE: "true"
  AGENT_MAX_ITERATIONS: "5"
  CACHE_ENABLED: "true"
  CACHE_TTL: "3600"
  RATE_LIMIT_RPM: "120"
  CORS_ORIGINS: "https://nexusrag.example.com"
  DATA_API_PORT: "3456"
  NODE_ENV: "production"
```

## Kubernetes Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: nexusrag-secrets
  namespace: nexusrag
type: Opaque
stringData:
  OPENAI_API_KEY: "sk-your-production-key"
  MONGO_URI: "mongodb+srv://<user>:<password>@<your-cluster>.mongodb.net"
  API_KEY: "production-data-api-key"
  REDIS_URL: "redis://redis:6379/0"
```

---

## Environment Precedence

Configuration values are resolved in the following order (highest precedence first):

1. Explicit environment variables set on the process
2. Docker Compose `environment` block
3. `.env` file (Docker Compose auto-loads; Gateway uses `python-dotenv`)
4. Application defaults defined in code

---

## Validation

The Gateway validates all configuration at startup. Missing required variables (e.g., `OPENAI_API_KEY` when `LLM_PROVIDER=openai`) cause the process to exit with a descriptive error message. Optional variables fall back to their documented defaults.

The Data API validates its configuration when the Express server initializes. Missing `MONGO_URI` causes the server to log an error and terminate.

The UI validates `VITE_GATEWAY_URL` at build time. If unset, the build succeeds but API calls default to `http://localhost:5000`.
