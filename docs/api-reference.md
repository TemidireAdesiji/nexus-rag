# NexusRAG API Reference

This document covers every endpoint exposed by the Gateway and Data API services, the WebSocket protocol, OpenAI-compatible completions, error formats, and rate limiting.

---

## Gateway API (port 5000)

### POST /api/inquire

Submit a query to the RAG pipeline and receive a complete response.

**Request:**

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "query": "What services does the team offer?",
    "strategy": "combined",
    "conversation_id": "conv_abc123",
    "options": {
      "top_k": 5,
      "rerank": true,
      "temperature": 0.7
    }
  }'
```

**Response (200):**

```json
{
  "answer": "The team offers a range of services including...",
  "sources": [
    {
      "chunk_id": "chunk_001",
      "document": "services-overview.pdf",
      "content": "Our core service areas include...",
      "score": 0.92,
      "page": 3
    },
    {
      "chunk_id": "chunk_042",
      "document": "capabilities-deck.pdf",
      "content": "In addition to consulting...",
      "score": 0.87,
      "page": 7
    }
  ],
  "strategy_used": "combined",
  "conversation_id": "conv_abc123",
  "turn_id": "turn_xyz789",
  "tokens": {
    "prompt": 1842,
    "completion": 256,
    "total": 2098
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `query` | string (required) | The user question |
| `strategy` | string (optional) | One of `vector`, `combined`, `expanded`, `decomposed`. Falls back to platform default. |
| `conversation_id` | string (optional) | Resume an existing conversation. Omit to start a new one. |
| `options.top_k` | integer (optional) | Override the number of chunks returned after reranking |
| `options.rerank` | boolean (optional) | Override the global reranking setting for this request |
| `options.temperature` | float (optional) | Override the LLM temperature for this request |

---

### POST /api/inquire/completions

OpenAI-compatible chat completions endpoint. Drop-in replacement for `POST https://api.openai.com/v1/chat/completions`.

**Request:**

```bash
curl -X POST http://localhost:5000/api/inquire/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d '{
    "model": "nexusrag",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Summarize the latest project outcomes."}
    ],
    "stream": false,
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

**Response (200):**

```json
{
  "id": "chatcmpl-nexus-abc123",
  "object": "chat.completion",
  "created": 1711800000,
  "model": "nexusrag",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Based on the retrieved documents, the latest project outcomes include..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1200,
    "completion_tokens": 300,
    "total_tokens": 1500
  }
}
```

When `stream: true`, the response is delivered as server-sent events (SSE) with `data: {...}` lines, followed by `data: [DONE]`.

---

### GET /api/conversations

List conversations for the authenticated user.

```bash
curl http://localhost:5000/api/conversations \
  -H "Authorization: Bearer $API_KEY"
```

**Response (200):**

```json
{
  "conversations": [
    {
      "id": "conv_abc123",
      "title": "Service Inquiry",
      "created_at": "2026-03-15T10:30:00Z",
      "updated_at": "2026-03-15T10:45:00Z",
      "turn_count": 4
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20
}
```

### GET /api/conversations/{id}

Retrieve a single conversation with all turns.

```bash
curl http://localhost:5000/api/conversations/conv_abc123 \
  -H "Authorization: Bearer $API_KEY"
```

**Response (200):**

```json
{
  "id": "conv_abc123",
  "title": "Service Inquiry",
  "created_at": "2026-03-15T10:30:00Z",
  "updated_at": "2026-03-15T10:45:00Z",
  "turns": [
    {
      "id": "turn_001",
      "role": "user",
      "content": "What services does the team offer?",
      "timestamp": "2026-03-15T10:30:00Z"
    },
    {
      "id": "turn_002",
      "role": "assistant",
      "content": "The team offers...",
      "sources": [...],
      "strategy": "combined",
      "timestamp": "2026-03-15T10:30:05Z"
    }
  ]
}
```

### DELETE /api/conversations/{id}

Delete a conversation and all its turns.

```bash
curl -X DELETE http://localhost:5000/api/conversations/conv_abc123 \
  -H "Authorization: Bearer $API_KEY"
```

**Response (204):** No content.

---

### POST /api/ingest

Ingest a document into the vector store.

```bash
curl -X POST http://localhost:5000/api/ingest \
  -H "Authorization: Bearer $API_KEY" \
  -F "file=@document.pdf" \
  -F "metadata={\"source\": \"internal\", \"category\": \"proposals\"}"
```

**Response (201):**

```json
{
  "document_id": "doc_def456",
  "filename": "document.pdf",
  "chunks_created": 42,
  "total_tokens": 18500,
  "ingested_at": "2026-03-15T11:00:00Z"
}
```

---

### GET /api/search-modes

List available retrieval strategies and their descriptions.

```bash
curl http://localhost:5000/api/search-modes
```

**Response (200):**

```json
{
  "modes": [
    {
      "id": "vector",
      "name": "Vector Search",
      "description": "Semantic similarity search using dense embeddings.",
      "default": false
    },
    {
      "id": "combined",
      "name": "Combined Search",
      "description": "Hybrid of vector and keyword (BM25) search with reciprocal rank fusion.",
      "default": true
    },
    {
      "id": "expanded",
      "name": "Expanded Search",
      "description": "LLM-generated query expansions for broader recall.",
      "default": false
    },
    {
      "id": "decomposed",
      "name": "Decomposed Search",
      "description": "Breaks complex queries into sub-questions for comprehensive retrieval.",
      "default": false
    }
  ]
}
```

---

### GET /api/platform/info

Return platform metadata and version information.

```bash
curl http://localhost:5000/api/platform/info
```

**Response (200):**

```json
{
  "platform": "NexusRAG",
  "version": "1.0.0",
  "environment": "production",
  "llm_provider": "openai",
  "llm_model": "gpt-4o",
  "vector_store": "faiss",
  "agentic_mode": true,
  "reranking_enabled": true
}
```

---

### GET /api/platform/tools

List registered agent tools (available when agentic mode is enabled).

```bash
curl http://localhost:5000/api/platform/tools
```

**Response (200):**

```json
{
  "tools": [
    {
      "name": "rag_search",
      "description": "Search the document corpus using a specified retrieval strategy.",
      "parameters": {
        "query": "string",
        "strategy": "string (optional)"
      }
    },
    {
      "name": "data_api_lookup",
      "description": "Query the Data API for structured records.",
      "parameters": {
        "endpoint": "string",
        "filters": "object (optional)"
      }
    }
  ]
}
```

---

### Health Probes

**GET /alive** -- Returns 200 if the process is running.

```bash
curl http://localhost:5000/alive
# {"status": "alive"}
```

**GET /ready** -- Returns 200 if all dependencies (MongoDB, vector store, LLM) are reachable.

```bash
curl http://localhost:5000/ready
# {"status": "ready", "checks": {"mongodb": "ok", "vector_store": "ok", "llm": "ok"}}
```

**GET /health** -- Returns detailed component health with timing information.

```bash
curl http://localhost:5000/health
# {"status": "healthy", "uptime": 3600, "components": {...}}
```

---

## WebSocket Protocol

### Connection

```
ws://localhost:5000/ws/chat
```

The client opens a WebSocket connection and exchanges JSON messages.

### Client-to-Server Messages

**Chat message:**

```json
{
  "type": "chat",
  "payload": {
    "query": "What are the key project outcomes?",
    "conversation_id": "conv_abc123",
    "strategy": "combined",
    "options": {
      "top_k": 5,
      "rerank": true
    }
  }
}
```

**Ping:**

```json
{
  "type": "ping"
}
```

### Server-to-Client Messages

**Token stream:**

```json
{
  "type": "token",
  "payload": {
    "content": "The",
    "turn_id": "turn_xyz789"
  }
}
```

**Stream complete:**

```json
{
  "type": "done",
  "payload": {
    "turn_id": "turn_xyz789",
    "sources": [...],
    "tokens": {
      "prompt": 1200,
      "completion": 300,
      "total": 1500
    }
  }
}
```

**Error:**

```json
{
  "type": "error",
  "payload": {
    "code": "retrieval_failed",
    "message": "Vector store is temporarily unavailable."
  }
}
```

**Pong:**

```json
{
  "type": "pong"
}
```

### Connection Lifecycle

1. Client connects to `/ws/chat`.
2. Server sends `{"type": "connected", "payload": {"session_id": "..."}}`.
3. Client sends `chat` messages; server responds with a sequence of `token` messages followed by a `done` message.
4. Either party can close the connection at any time.
5. The server sends a `ping` every 30 seconds. If the client does not respond with a `pong` within 10 seconds, the server closes the connection.

---

## Data API (port 3456)

### GET /auth/credential

Obtain an API credential for subsequent requests.

```bash
curl http://localhost:3456/auth/credential
```

**Response (200):**

```json
{
  "api_key": "nxr_live_abc123...",
  "expires_at": "2026-04-15T00:00:00Z"
}
```

### GET /api/personnel

Retrieve team member profiles.

```bash
curl http://localhost:3456/api/personnel \
  -H "Authorization: Bearer $DATA_API_KEY"
```

**Response (200):**

```json
{
  "personnel": [
    {
      "id": "p_001",
      "name": "Jane Smith",
      "role": "Lead Engineer",
      "bio": "10+ years in distributed systems...",
      "skills": ["Python", "Kubernetes", "ML"],
      "avatar_url": "https://cdn.example.com/avatars/jane.png"
    }
  ]
}
```

### GET /api/portfolio

Retrieve project case studies.

```bash
curl http://localhost:3456/api/portfolio \
  -H "Authorization: Bearer $DATA_API_KEY"
```

**Response (200):**

```json
{
  "portfolio": [
    {
      "id": "proj_001",
      "title": "Enterprise Search Platform",
      "description": "Built a semantic search engine for...",
      "technologies": ["Python", "FAISS", "React"],
      "outcomes": "40% improvement in search relevance",
      "vertical": "Technology"
    }
  ]
}
```

### GET /api/verticals

Retrieve industry verticals.

```bash
curl http://localhost:3456/api/verticals \
  -H "Authorization: Bearer $DATA_API_KEY"
```

**Response (200):**

```json
{
  "verticals": [
    {
      "id": "v_001",
      "name": "Financial Services",
      "description": "Banking, insurance, and fintech solutions",
      "portfolio_count": 8
    }
  ]
}
```

### GET /api/engagements

Retrieve engagement records.

```bash
curl http://localhost:3456/api/engagements \
  -H "Authorization: Bearer $DATA_API_KEY"
```

**Response (200):**

```json
{
  "engagements": [
    {
      "id": "eng_001",
      "client": "Acme Corp",
      "vertical": "Technology",
      "status": "active",
      "start_date": "2025-06-01",
      "end_date": null
    }
  ]
}
```

### GET /api/corpus/download

Download the full document corpus as a compressed archive.

```bash
curl -O http://localhost:3456/api/corpus/download \
  -H "Authorization: Bearer $DATA_API_KEY"
```

**Response (200):** Binary stream with `Content-Type: application/gzip`.

### GET /ping

Health check endpoint.

```bash
curl http://localhost:3456/ping
# {"status": "pong", "timestamp": "2026-03-15T12:00:00Z"}
```

---

## Error Format

All endpoints return errors in a consistent JSON format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The 'query' field is required.",
    "details": [
      {
        "field": "query",
        "issue": "missing"
      }
    ],
    "request_id": "req_abc123"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `validation_error` | 400 | Request body failed schema validation |
| `unauthorized` | 401 | Missing or invalid Authorization header |
| `forbidden` | 403 | Valid credentials but insufficient permissions |
| `not_found` | 404 | Requested resource does not exist |
| `rate_limited` | 429 | Too many requests; retry after the indicated duration |
| `retrieval_failed` | 502 | Vector store or reranker returned an error |
| `llm_error` | 502 | LLM provider returned an error |
| `timeout` | 504 | Request exceeded the configured timeout |
| `internal_error` | 500 | Unexpected server error |

---

## Rate Limit Headers

Every Gateway response includes rate limit headers:

```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 117
X-RateLimit-Reset: 1711800060
Retry-After: 30
```

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed per minute |
| `X-RateLimit-Remaining` | Requests remaining in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the window resets |
| `Retry-After` | Seconds to wait before retrying (only present on 429 responses) |
