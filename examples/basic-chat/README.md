# Basic Chat Example

This guide walks through a complete chat interaction with NexusRAG using only curl commands. You will start the services, create a conversation, send messages, and view the retrieved sources.

---

## Prerequisites

- Docker and Docker Compose installed
- A valid OpenAI API key
- curl installed

---

## Step 1: Start the Services

From the NexusRAG project root:

```bash
# Create a minimal .env file
cat > .env <<'EOF'
OPENAI_API_KEY=sk-your-key-here
MONGO_URI=mongodb://mongo:27017
CORS_ORIGINS=*
DEFAULT_SEARCH_MODE=vector
EOF

# Start all services
docker compose up -d

# Wait for services to be ready
echo "Waiting for services..."
until curl -sf http://localhost:5000/ready > /dev/null 2>&1; do sleep 2; done
echo "Gateway is ready."

until curl -sf http://localhost:3456/ping > /dev/null 2>&1; do sleep 2; done
echo "Data API is ready."
```

Verify:

```bash
curl -s http://localhost:5000/api/platform/info | python3 -m json.tool
```

Expected output includes platform name, version, and enabled features.

---

## Step 2: Ingest a Document (Optional)

If the corpus is not pre-loaded, ingest a document:

```bash
curl -X POST http://localhost:5000/api/ingest \
  -F "file=@sample-document.pdf" \
  -F 'metadata={"source": "example", "category": "general"}'
```

Expected response:

```json
{
  "document_id": "doc_abc123",
  "filename": "sample-document.pdf",
  "chunks_created": 15,
  "total_tokens": 6200,
  "ingested_at": "2026-03-30T12:00:00Z"
}
```

---

## Step 3: Send Your First Query

Send a query without specifying a conversation ID. The system will create a new conversation automatically.

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main services offered?"
  }'
```

Expected response:

```json
{
  "answer": "Based on the available documents, the main services offered include...",
  "sources": [
    {
      "chunk_id": "chunk_001",
      "document": "sample-document.pdf",
      "content": "Our primary service areas encompass...",
      "score": 0.94,
      "page": 2
    },
    {
      "chunk_id": "chunk_007",
      "document": "sample-document.pdf",
      "content": "Additionally, we provide...",
      "score": 0.88,
      "page": 5
    }
  ],
  "strategy_used": "vector",
  "conversation_id": "conv_new123",
  "turn_id": "turn_001",
  "tokens": {
    "prompt": 1200,
    "completion": 180,
    "total": 1380
  }
}
```

Note the `conversation_id` in the response. You will use it in the next step to continue the conversation.

---

## Step 4: Continue the Conversation

Use the `conversation_id` from the previous response to send a follow-up message:

```bash
curl -X POST http://localhost:5000/api/inquire \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Can you tell me more about the consulting practice?",
    "conversation_id": "conv_new123"
  }'
```

The Gateway includes the previous turn in the prompt context, enabling the LLM to provide a coherent follow-up answer.

---

## Step 5: View Conversation History

Retrieve the full conversation to see all turns and their sources:

```bash
curl -s http://localhost:5000/api/conversations/conv_new123 | python3 -m json.tool
```

Expected output:

```json
{
  "id": "conv_new123",
  "title": "Service Inquiry",
  "created_at": "2026-03-30T12:00:00Z",
  "updated_at": "2026-03-30T12:01:00Z",
  "turns": [
    {
      "id": "turn_001",
      "role": "user",
      "content": "What are the main services offered?",
      "timestamp": "2026-03-30T12:00:00Z"
    },
    {
      "id": "turn_002",
      "role": "assistant",
      "content": "Based on the available documents, the main services offered include...",
      "sources": [
        {
          "chunk_id": "chunk_001",
          "document": "sample-document.pdf",
          "content": "Our primary service areas encompass...",
          "score": 0.94
        }
      ],
      "strategy": "vector",
      "timestamp": "2026-03-30T12:00:05Z"
    },
    {
      "id": "turn_003",
      "role": "user",
      "content": "Can you tell me more about the consulting practice?",
      "timestamp": "2026-03-30T12:01:00Z"
    },
    {
      "id": "turn_004",
      "role": "assistant",
      "content": "The consulting practice focuses on...",
      "sources": [...],
      "strategy": "vector",
      "timestamp": "2026-03-30T12:01:04Z"
    }
  ]
}
```

---

## Step 6: Inspect Retrieved Sources

Each assistant turn includes a `sources` array. These are the document chunks that the retrieval pipeline found most relevant to the query. Each source includes:

- **chunk_id** -- Unique identifier for the chunk in the vector store.
- **document** -- The original filename.
- **content** -- The full text of the chunk.
- **score** -- Relevance score (0 to 1, higher is better). If reranking is enabled, this is the reranker score; otherwise, it is the cosine similarity from vector search.
- **page** -- Page number in the original document (if available).

You can use this information to verify the answer is grounded in the source material.

---

## Step 7: List All Conversations

```bash
curl -s http://localhost:5000/api/conversations | python3 -m json.tool
```

---

## Step 8: Delete a Conversation

```bash
curl -X DELETE http://localhost:5000/api/conversations/conv_new123
# Returns 204 No Content on success
```

---

## Step 9: Try the OpenAI-Compatible Endpoint

If you have existing code that uses the OpenAI SDK, you can point it at NexusRAG:

```bash
curl -X POST http://localhost:5000/api/inquire/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nexusrag",
    "messages": [
      {"role": "user", "content": "Summarize the key project outcomes."}
    ],
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

The response follows the OpenAI Chat Completions format.

---

## Cleanup

```bash
docker compose down -v
```

This stops all services and removes the volumes (including MongoDB data and the vector store).
