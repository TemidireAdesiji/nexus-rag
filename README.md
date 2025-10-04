# NexusRAG

Production-grade Retrieval-Augmented Generation platform that combines agentic orchestration with multi-strategy document retrieval to deliver accurate, source-cited answers from your own data.

[![CI/CD](https://img.shields.io/github/actions/workflow/status/OWNER/nexus-rag/ci.yml?branch=main&label=build)](https://github.com/OWNER/nexus-rag/actions)
[![Coverage](https://img.shields.io/badge/coverage-88%25-brightgreen)](https://github.com/OWNER/nexus-rag)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue)](CHANGELOG.md)

---

## Overview

Most RAG implementations treat retrieval as a single-strategy problem. In practice, different questions demand different retrieval approaches: a factual lookup benefits from pure vector similarity, while a complex analytical query needs decomposition into sub-questions before meaningful context can be assembled. NexusRAG addresses this by exposing four distinct retrieval strategies through a unified API, letting callers choose the right approach per query.

The platform is built as three cooperating services. A Python/FastAPI gateway handles the core RAG pipeline -- ingestion, retrieval, cross-encoder reranking, LLM generation, and agentic tool orchestration. A Node.js/Express data API manages structured business data (team profiles, portfolio investments, sector intelligence, consultation records) and serves a downloadable document corpus. A React frontend provides a conversational interface with session management, strategy selection, and inline source citations.

NexusRAG is designed for teams that need a self-hosted RAG system with fine-grained control over retrieval behavior, transparent source attribution, and the flexibility to integrate structured API data alongside unstructured document knowledge. It runs locally via Docker Compose and scales to production on Kubernetes with Terraform-managed infrastructure.

## Key Features

- **Four retrieval strategies** -- vector similarity, hybrid vector+keyword, multi-query expansion, and query decomposition -- selectable per request
- **Cross-encoder reranking** using sentence-transformers to surface the most relevant passages after initial retrieval
- **Agentic tool orchestration** that automatically queries structured data APIs when the question involves known entities (team members, portfolio companies, sectors)
- **OpenAI-compatible endpoint** at `/api/inquire/completions` for drop-in integration with existing toolchains
- **WebSocket streaming** that delivers answers in real-time chunks with progress events
- **Session management** with conversation history, enabling multi-turn interactions with context carry-over
- **Document ingestion pipeline** supporting PDF, DOCX, TXT, and Markdown with configurable chunking
- **Production-ready deployment** with Docker Compose, Kubernetes manifests, Terraform modules, health probes, and rate limiting

## Quick Start

```bash
# Clone the repository
git clone https://github.com/OWNER/nexus-rag.git
cd nexus-rag

# Set your OpenAI API key (or configure Ollama for local LLM)
export OPENAI_API_KEY=sk-your-key-here

# Start all services
docker compose up --build -d

# Open the UI
open http://localhost:3000
```

The gateway will be available at `http://localhost:5000`, the data API at `http://localhost:3456`, and the UI at `http://localhost:3000`. The first startup takes a few minutes while models are downloaded and the vector store is initialized.

## Architecture

```
                          +------------------+
                          |    UI (React)    |
                          |   localhost:3000  |
                          +--------+---------+
                                   |
                    HTTP / WebSocket|
                                   v
                          +--------+---------+
                          | Gateway (FastAPI) |
                          |  localhost:5000   |
                          +--+-----+------+--+
                             |     |      |
              +--------------+     |      +---------------+
              |                    |                      |
              v                    v                      v
    +---------+------+   +---------+-------+   +----------+--------+
    |  ChromaDB      |   |  Data API       |   |  Redis Cache      |
    |  (Vector Store)|   |  (Express/Mongo) |   |  (Sessions/Rate)  |
    |                |   |  localhost:3456  |   |  localhost:6379    |
    +----------------+   +--------+--------+   +-------------------+
                                  |
                                  v
                         +--------+--------+
                         |    MongoDB      |
                         |  localhost:27017 |
                         +-----------------+
```

## Configuration

Each service is configured through environment variables. Key settings:

| Variable | Service | Default | Purpose |
|---|---|---|---|
| `OPENAI_API_KEY` | Gateway | -- | API key for OpenAI models |
| `LLM_MODEL_NAME` | Gateway | `llama3` | LLM model identifier |
| `EMBEDDING_MODEL_NAME` | Gateway | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `DATA_API_URL` | Gateway | `http://localhost:5000` | Data API base URL |
| `MONGODB_URI` | Data API | `mongodb://localhost:27017/nexus_rag` | MongoDB connection string |
| `VITE_API_URL` | UI | `/api` | Gateway API base URL |

See [docs/configuration.md](docs/configuration.md) for the complete configuration reference.

## Usage Examples

**Ask a question with vector search:**

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the go-to-market strategy for enterprise SaaS?",
    "strategy": "vector"
  }'
```

**Use the OpenAI-compatible endpoint:**

```bash
curl -X POST http://localhost:5000/api/inquire/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Summarize the M&A strategy"}],
    "model": "nexus-rag",
    "strategy": "combined"
  }'
```

**Upload a document for indexing:**

```bash
curl -X POST http://localhost:5000/api/ingest \
  -F "file=@/path/to/document.pdf"
```

## Development

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker and Docker Compose
- An LLM provider (OpenAI API key or local Ollama instance)

### Setup

```bash
# Gateway
cd services/gateway
pip install -e ".[dev]"

# Data API
cd services/data-api
npm install

# UI
cd services/ui
npm install
```

### Running Tests

```bash
# Gateway tests
cd services/gateway
pytest --cov=gateway

# Data API tests
cd services/data-api
npm test
```

### Project Structure

```
nexus-rag/
  docker-compose.yml          # Local orchestration
  services/
    gateway/                   # Python/FastAPI RAG engine
      gateway/
        agents/                # Agentic planner, executor, tool registry
        clients/               # Data API HTTP client
        generation/            # LLM interface, prompt templates, answer composer
        middleware/             # Auth, logging, request ID
        retrieval/              # Strategies, indexer, reranker, loader
        routes/                # HTTP + WebSocket endpoints
        storage/               # Redis cache, rate limiter, sessions
        config.py              # Pydantic settings
        models.py              # Request/response schemas
        orchestrator.py        # Central RAG coordinator
      tests/
    data-api/                  # Node.js/Express data service
      src/
        models/                # Mongoose schemas
        routes/                # REST endpoints
        middleware/             # Auth, validation, error handling
        data/                  # Seed data
      documents/               # Corpus text files
      tests/
    ui/                        # React/Vite frontend
      src/
        components/            # Chat, sessions, system panels
        hooks/                 # useChat, useSession, useSocket
        lib/                   # API client
  deploy/
    k8s/                       # Kubernetes manifests (Kustomize)
  docs/                        # Extended documentation
  examples/                    # Usage examples
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting patches, reporting issues, and the development workflow.

## Roadmap

- [x] Multi-strategy retrieval (vector, combined, expanded, decomposed)
- [x] Cross-encoder reranking
- [x] Agentic tool orchestration
- [x] OpenAI-compatible API
- [x] WebSocket streaming
- [x] Docker Compose deployment
- [x] Kubernetes manifests
- [ ] GPU-accelerated inference support
- [ ] Multi-tenant isolation
- [ ] Evaluation framework with RAGAS metrics
- [ ] Hybrid cloud deployment (AWS + OCI)
- [ ] Plugin system for custom retrieval strategies
- [ ] Observability dashboard with Grafana

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

## Acknowledgments

NexusRAG builds on a foundation of excellent open-source projects: LangChain for the retrieval and generation pipeline, FastAPI and Express for the service layer, ChromaDB for vector storage, and sentence-transformers for embedding and reranking models. The frontend uses React with Material UI. Infrastructure tooling relies on Docker, Kubernetes, and Terraform.
