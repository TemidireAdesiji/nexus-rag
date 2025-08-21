# NexusRAG Gateway

The Gateway is the core intelligence service of the NexusRAG platform. It implements the full RAG pipeline -- retrieval, reranking, generation -- and exposes it through HTTP and WebSocket APIs.

---

## Responsibilities

- Accept user queries and route them through the configured retrieval strategy
- Manage four retrieval strategies: vector, combined, expanded, and decomposed
- Rerank retrieved chunks using a cross-encoder model
- Generate answers via an LLM (OpenAI, Azure OpenAI, or local endpoint)
- Provide an OpenAI-compatible chat completions endpoint
- Stream responses over WebSocket for real-time chat experiences
- Manage conversation history (CRUD) in MongoDB
- Ingest documents into the vector store
- Orchestrate agentic tool-calling loops when enabled
- Expose health, readiness, and liveness probes

---

## Architecture

```
gateway/
  agents/         # Agentic orchestration and tool registry
  clients/        # External service clients (LLM, Data API)
  generation/     # LLM interaction, prompt construction
  middleware/     # CORS, rate limiting, error handling
  retrieval/      # Retrieval strategies and vector store adapters
  routes/         # FastAPI route handlers
  storage/        # MongoDB and vector store persistence
  config.py       # Configuration loading and validation
  entities.py     # Domain entities (Conversation, Turn, Document)
  models.py       # Pydantic request/response models
  orchestrator.py # Pipeline orchestration (retrieval -> reranking -> generation)
  server.py       # FastAPI app factory
  main.py         # Entry point
```

---

## Quick Start

### With Docker

```bash
# From the project root
docker compose up gateway
```

### Without Docker

```bash
cd services/gateway

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set required environment variables
export OPENAI_API_KEY=sk-your-key
export MONGO_URI=mongodb://localhost:27017

# Start the server
python -m gateway.main
```

The Gateway starts on port 5000 by default.

---

## Configuration

All configuration is via environment variables. Key settings:

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_PORT` | `5000` | Server port |
| `GATEWAY_WORKERS` | `1` | Uvicorn worker count |
| `OPENAI_API_KEY` | -- | OpenAI API key (required) |
| `OPENAI_MODEL` | `gpt-4o` | LLM model identifier |
| `DEFAULT_SEARCH_MODE` | `vector` | Default retrieval strategy |
| `RERANKING_ENABLED` | `true` | Enable cross-encoder reranking |
| `AGENTIC_MODE` | `false` | Enable agentic orchestration |
| `MONGO_URI` | `mongodb://localhost:27017` | MongoDB connection string |

See `docs/configuration.md` for the complete reference.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/inquire` | Submit a RAG query |
| POST | `/api/inquire/completions` | OpenAI-compatible completions |
| GET | `/api/conversations` | List conversations |
| GET | `/api/conversations/{id}` | Get a conversation |
| DELETE | `/api/conversations/{id}` | Delete a conversation |
| POST | `/api/ingest` | Ingest a document |
| GET | `/api/search-modes` | List retrieval strategies |
| GET | `/api/platform/info` | Platform metadata |
| GET | `/api/platform/tools` | List agent tools |
| WS | `/ws/chat` | WebSocket chat |
| GET | `/alive` | Liveness probe |
| GET | `/ready` | Readiness probe |
| GET | `/health` | Detailed health check |

See `docs/api-reference.md` for full request/response documentation.

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gateway --cov-report=html

# Run a specific test module
pytest tests/retrieval/test_vector_strategy.py
```

---

## Development

### Adding a Retrieval Strategy

1. Create a class in `gateway/retrieval/` that extends `RetrievalStrategy`.
2. Implement the `retrieve(query, top_k)` method.
3. Register the class in the strategy registry.
4. See `docs/development.md` for a detailed walkthrough.

### Adding an Agent Tool

1. Create a class in `gateway/agents/` that extends `AgentTool`.
2. Implement the `execute()` method.
3. Register in the tool registry.
4. Add the tool name to the `AGENT_TOOLS` environment variable.

---

## Docker

```bash
# Build
docker build -t nexusrag-gateway -f Dockerfile .

# Run
docker run -p 5000:5000 \
  -e OPENAI_API_KEY=sk-your-key \
  -e MONGO_URI=mongodb://host.docker.internal:27017 \
  nexusrag-gateway
```

The Dockerfile uses a multi-stage build to keep the production image small. The final image is based on `python:3.12-slim`.
