# NexusRAG Architecture

## Overview

NexusRAG is a production-grade Retrieval-Augmented Generation (RAG) platform designed to serve intelligent, context-aware conversational experiences over domain-specific corpora. The system is composed of three independently deployable services that communicate over HTTP and WebSocket protocols, backed by MongoDB for persistence and a vector store for semantic retrieval.

This document describes the design principles, service decomposition, data flows, RAG internals, security posture, and extension points that define the platform.

---

## Design Principles

1. **Strategy-First Retrieval** -- The platform does not prescribe a single retrieval path. Four distinct strategies (vector, combined, expanded, decomposed) allow callers to trade latency for recall depending on the use case.

2. **Agentic Orchestration** -- A lightweight agent layer sits above the retrieval strategies and can autonomously decide which tools to invoke, when to re-query, and how to synthesize a final answer.

3. **Service Isolation** -- Each service owns its data and exposes a well-defined API contract. The Gateway never writes directly to MongoDB collections owned by the Data API, and the UI never calls MongoDB at all.

4. **OpenAI-Compatible Surface** -- The Gateway exposes an `/api/inquire/completions` endpoint that mirrors the OpenAI Chat Completions contract, making it a drop-in replacement for applications already integrated with the OpenAI SDK.

5. **Progressive Deployment** -- Every service ships as a multi-architecture Docker image with health, readiness, and liveness probes, enabling canary and blue-green rollouts in Kubernetes.

---

## System Diagram

```
                         +---------------------+
                         |     Browser / CLI    |
                         +----------+----------+
                                    |
                          HTTP / WebSocket
                                    |
                    +---------------v----------------+
                    |         NGINX / Ingress        |
                    +---+---------------+--------+---+
                        |               |        |
               +--------v---+   +------v----+  +v-----------+
               |   Gateway   |   |  Data API |  |     UI     |
               |  (FastAPI)  |   | (Express) |  | (React/    |
               |  port 5000  |   | port 3456 |  |  Vite/MUI) |
               +--+----+---+-+   +-----+-----+  | port 3000  |
                  |    |   |           |         +------------+
                  |    |   |           |
          +-------v-+  |  +----+  +---v--------+
          | Vector   |  |      |  |  MongoDB    |
          | Store    |  |      |  | (documents, |
          | (FAISS / |  |      |  |  teams,     |
          |  Chroma) |  |      |  |  corpus)    |
          +----------+  |      |  +-------------+
                        |      |
               +--------v-+ +--v-----------+
               |   LLM     | | Reranker     |
               | (OpenAI / | | (cross-enc.  |
               |  local)   | |  or API)     |
               +-----------+ +-------------+
```

---

## Service Responsibilities

### Gateway (FastAPI -- port 5000)

The Gateway is the intelligence layer of the platform. It owns:

- **Retrieval pipeline** -- Accepts a user query, selects a retrieval strategy, fetches candidate chunks from the vector store, optionally reranks them, and feeds the top-k context to the LLM.
- **Agentic orchestration** -- When enabled, the agent loop can invoke registered tools (search, calculator, data-api lookup) across multiple turns before producing a final answer.
- **Conversation management** -- CRUD operations on conversation objects stored in its own MongoDB collection.
- **Ingestion** -- Accepts documents via `POST /api/ingest`, splits them into chunks, computes embeddings, and writes them to the vector store.
- **WebSocket streaming** -- Provides a `/ws/chat` endpoint for token-by-token streaming of LLM responses.
- **OpenAI-compatible completions** -- `POST /api/inquire/completions` follows the OpenAI request/response schema so existing tooling can point at NexusRAG without modification.
- **Health probes** -- `/alive` (process up), `/ready` (dependencies reachable), `/health` (detailed component status).

### Data API (Express/MongoDB -- port 3456)

The Data API is the structured-data service. It owns:

- **Personnel / Team** -- `GET /api/personnel` returns team member profiles.
- **Portfolio** -- `GET /api/portfolio` returns project case studies.
- **Verticals** -- `GET /api/verticals` returns industry vertical metadata.
- **Engagements** -- `GET /api/engagements` returns active and historical engagements.
- **Corpus download** -- `GET /api/corpus/download` streams the full document corpus as a downloadable archive.
- **Authentication seed** -- `GET /auth/credential` provides initial credential exchange for API consumers.
- **Liveness** -- `GET /ping` returns a simple pong.

### UI (React / Vite / MUI -- port 3000)

The UI is a single-page application that provides:

- **Chat interface** -- A conversational UI that streams responses from the Gateway via WebSocket or SSE fallback.
- **Strategy selector** -- Users can pick a retrieval strategy before sending a query.
- **Source viewer** -- After each response, the UI displays the retrieved source chunks with relevance scores.
- **Conversation history** -- Sidebar listing past conversations with the ability to resume or delete them.

---

## Data Flow

### Ingestion Pipeline

1. A client sends a document payload to `POST /api/ingest` on the Gateway.
2. The Gateway validates the payload (file type, size limits, metadata).
3. The document is split into chunks using a recursive character text splitter with configurable chunk size and overlap.
4. Each chunk is passed through the embedding model to produce a dense vector.
5. Chunks and their vectors are written to the vector store (FAISS index on disk or Chroma collection).
6. A metadata record is stored in MongoDB linking the document ID to its chunk IDs and ingestion timestamp.
7. The Gateway returns a summary (document ID, chunk count, token count).

### Query Pipeline

1. A user sends a query to `POST /api/inquire` (or via the WebSocket at `/ws/chat`).
2. The Gateway resolves the retrieval strategy (from the request body, session default, or platform default).
3. The selected strategy executes:
   - **Vector** -- Embeds the query, performs ANN search against the vector store, returns top-k chunks.
   - **Combined** -- Runs both vector search and keyword (BM25) search, merges results with reciprocal rank fusion.
   - **Expanded** -- Uses the LLM to generate query expansions (synonyms, related phrases), runs vector search for each expansion, deduplicates and merges.
   - **Decomposed** -- Uses the LLM to break a complex query into sub-questions, retrieves context for each, then synthesizes a unified answer.
4. If reranking is enabled, the candidate chunks are scored by a cross-encoder reranker and re-sorted.
5. The top-k reranked chunks are assembled into a prompt template alongside the conversation history.
6. The prompt is sent to the LLM (OpenAI API or a local model endpoint).
7. The response is streamed back to the client token-by-token (WebSocket) or returned as a complete JSON payload (HTTP).
8. The conversation turn (query, response, sources, strategy used) is persisted to MongoDB.

---

## RAG Internals

### Retrieval Strategies

| Strategy     | Latency | Recall | Best For                                  |
|------------- |---------|--------|-------------------------------------------|
| vector       | Low     | Good   | Straightforward factual queries           |
| combined     | Medium  | Better | Queries with specific terminology          |
| expanded     | High    | Higher | Vague or short queries                     |
| decomposed   | Highest | Best   | Multi-part or comparative questions        |

The strategy is selected per request via the `strategy` field in the request body. If omitted, the platform default (configurable via `DEFAULT_SEARCH_MODE`) is used.

### Reranking

After initial retrieval, an optional reranking step rescores each candidate chunk using a cross-encoder model. This produces more accurate relevance ordering at the cost of additional latency. Reranking is controlled by:

- `RERANKING_ENABLED` (boolean, default `true`)
- `RERANKER_MODEL` (string, default `cross-encoder/ms-marco-MiniLM-L-6-v2`)
- `RERANKER_TOP_K` (integer, default `5`)

### Generation

The generation step constructs a prompt from a Jinja2 template that includes:

- System instructions (persona, tone, citation requirements)
- Retrieved context chunks with source metadata
- Conversation history (last N turns, configurable)
- The current user query

The prompt is sent to the configured LLM endpoint. Streaming is supported via server-sent events internally, which the Gateway relays over WebSocket or HTTP chunked transfer encoding.

---

## Agentic Orchestration

When agentic mode is enabled (`AGENTIC_MODE=true`), the Gateway wraps the retrieval-generation pipeline inside a tool-using agent loop:

1. The agent receives the user query and a list of available tools.
2. It decides whether to answer directly or invoke a tool.
3. Available tools include:
   - `rag_search` -- Executes the retrieval pipeline with a specified strategy.
   - `data_api_lookup` -- Calls the Data API to fetch structured records.
   - `calculator` -- Evaluates arithmetic expressions.
   - Custom tools registered via the plugin interface.
4. The agent can invoke multiple tools in sequence, using the output of one as input to the next.
5. After the agent determines it has sufficient context, it produces a final answer.
6. The full tool-call trace is returned alongside the answer for transparency.

The agent loop is bounded by `AGENT_MAX_ITERATIONS` (default `5`) to prevent runaway execution.

---

## Data Model

### Gateway Collections (MongoDB)

- **conversations** -- `{ _id, user_id, title, created_at, updated_at, turns: [{ role, content, sources, strategy, timestamp }] }`
- **documents** -- `{ _id, filename, chunk_ids, ingested_at, metadata }`

### Data API Collections (MongoDB)

- **personnel** -- `{ _id, name, role, bio, skills, avatar_url }`
- **portfolio** -- `{ _id, title, description, technologies, outcomes, vertical }`
- **verticals** -- `{ _id, name, description, portfolio_count }`
- **engagements** -- `{ _id, client, vertical, status, start_date, end_date }`
- **corpus** -- `{ _id, document_id, content, metadata }`

---

## Security Model

- **Authentication** -- The Data API issues credentials via `GET /auth/credential`. API keys are passed in the `Authorization` header as Bearer tokens.
- **Transport** -- All inter-service communication should be TLS-encrypted in production. The Ingress terminates TLS and forwards plaintext to services within the cluster network.
- **CORS** -- The Gateway and Data API both enforce CORS origin whitelisting via `CORS_ORIGINS`.
- **Rate Limiting** -- The Gateway applies per-IP rate limiting (configurable via `RATE_LIMIT_RPM`). Rate limit state is stored in-memory by default or in Redis when `REDIS_URL` is set.
- **Input Validation** -- All request bodies are validated by Pydantic models (Gateway) or Joi schemas (Data API) before processing.
- **Secrets** -- API keys, database URIs, and LLM tokens are injected via environment variables and should never be committed to source control. See `deploy/docs/SECRETS_MANAGEMENT.md` for production recommendations.

---

## Scalability

- **Horizontal scaling** -- Each service is stateless (session state lives in MongoDB) and can be scaled independently behind a load balancer.
- **Vector store sharding** -- For corpora exceeding single-node memory, the vector store can be swapped to a distributed backend (e.g., Qdrant, Weaviate) by implementing the `VectorStoreAdapter` interface.
- **Connection pooling** -- Both the Gateway (Motor) and Data API (Mongoose) maintain connection pools to MongoDB. Pool sizes are configurable via `MONGO_POOL_SIZE`.
- **Caching** -- The Gateway supports an optional Redis cache for embedding lookups and reranker scores, reducing redundant computation for repeated queries.

---

## Failure Modes

| Failure                         | Impact                              | Mitigation                                          |
|---------------------------------|-------------------------------------|-----------------------------------------------------|
| LLM endpoint unreachable        | No generation; retrieval still works | Circuit breaker with fallback to cached responses    |
| Vector store corruption         | Retrieval returns empty results      | Periodic snapshots; rebuild from ingestion log       |
| MongoDB unavailable             | No conversation persistence          | Retry with exponential backoff; read-only mode       |
| Data API down                   | Agentic `data_api_lookup` fails      | Agent skips tool; answers from RAG context only      |
| Reranker model OOM              | Reranking step fails                 | Graceful fallback to un-reranked retrieval results   |

---

## Extension Points

1. **Custom retrieval strategies** -- Implement the `RetrievalStrategy` base class and register it in the strategy registry. See `docs/development.md` for a walkthrough.

2. **Custom agent tools** -- Implement the `AgentTool` interface (name, description, schema, execute) and register via the tool registry.

3. **Vector store backends** -- Implement the `VectorStoreAdapter` interface to add support for additional vector databases.

4. **Prompt templates** -- Override the default Jinja2 templates in the `templates/` directory to customize system instructions, citation format, or response style.

5. **Middleware** -- The FastAPI Gateway supports standard ASGI middleware. Add authentication providers, request logging, or tracing middleware in `gateway/middleware/`.

6. **UI themes** -- The MUI theme is defined in `src/theme.ts` and can be overridden to match organizational branding.
