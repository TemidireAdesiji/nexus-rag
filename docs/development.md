# NexusRAG Developer Guide

This guide covers the internal architecture, extension patterns, testing strategy, and debugging techniques for developers contributing to NexusRAG.

---

## Architecture Decisions

### Why FastAPI for the Gateway?

FastAPI provides native async support, automatic OpenAPI schema generation, Pydantic-based request validation, and first-class WebSocket handling. These features align directly with the Gateway's requirements: async LLM calls, typed request/response contracts, and streaming chat.

### Why Express for the Data API?

The Data API is a straightforward CRUD service over MongoDB. Express with Mongoose provides a mature, well-understood stack for this kind of workload. Keeping it in Node.js also simplifies the frontend developer experience when contributing across the UI and Data API.

### Why Separate Services?

The Gateway and Data API have fundamentally different scaling characteristics. The Gateway is CPU-bound (embedding computation, reranking) and benefits from GPU-accelerated nodes. The Data API is I/O-bound and scales cheaply on small instances. Separating them allows independent scaling and deployment cadences.

### Why FAISS as the Default Vector Store?

FAISS provides excellent single-node performance with no external dependencies. For teams that need a distributed vector store, the `VectorStoreAdapter` interface allows plugging in Chroma, Qdrant, or other backends without changing the retrieval pipeline.

---

## Project Structure

```
services/
  gateway/
    gateway/
      api/              # FastAPI route handlers
      core/             # Configuration, dependencies, middleware
      models/           # Pydantic request/response models
      retrieval/        # Retrieval strategies
      reranking/        # Cross-encoder reranking
      agent/            # Agentic orchestration, tool registry
      generation/       # LLM interaction, prompt templates
      ingestion/        # Document processing, chunking, embedding
      vectorstore/      # Vector store adapters
      templates/        # Jinja2 prompt templates
    tests/
    pyproject.toml
    Dockerfile
  data-api/
    src/
      routes/           # Express route handlers
      models/           # Mongoose schemas
      middleware/        # Auth, validation, error handling
      services/         # Business logic
    tests/
    package.json
    Dockerfile
  ui/
    src/
      components/       # React components
      hooks/            # Custom React hooks
      services/         # API client, WebSocket client
      theme.ts          # MUI theme
    public/
    package.json
    Dockerfile
```

---

## Adding a New Retrieval Strategy

The retrieval system is designed around the Strategy pattern. Each strategy implements a common interface and is registered in a central registry.

### Step 1: Create the Strategy Class

Create a new file in `services/gateway/gateway/retrieval/`:

```python
# services/gateway/gateway/retrieval/my_strategy.py
from gateway.retrieval.base import RetrievalStrategy, RetrievalResult

class MyStrategy(RetrievalStrategy):
    """
    A custom retrieval strategy that does something novel.
    """

    name = "my_strategy"
    description = "Brief description of what this strategy does."

    async def retrieve(self, query: str, top_k: int = 10) -> list[RetrievalResult]:
        # 1. Transform or augment the query
        augmented = self._preprocess(query)

        # 2. Search the vector store
        candidates = await self.vector_store.search(augmented, top_k=top_k)

        # 3. Post-process results
        results = [
            RetrievalResult(
                chunk_id=c.id,
                content=c.content,
                score=c.score,
                metadata=c.metadata,
            )
            for c in candidates
        ]
        return results

    def _preprocess(self, query: str) -> str:
        # Custom preprocessing logic
        return query
```

### Step 2: Register the Strategy

Add the strategy to the registry in `services/gateway/gateway/retrieval/__init__.py`:

```python
from gateway.retrieval.my_strategy import MyStrategy

STRATEGY_REGISTRY = {
    "vector": VectorStrategy,
    "combined": CombinedStrategy,
    "expanded": ExpandedStrategy,
    "decomposed": DecomposedStrategy,
    "my_strategy": MyStrategy,  # Add here
}
```

### Step 3: Write Tests

```python
# services/gateway/tests/retrieval/test_my_strategy.py
import pytest
from gateway.retrieval.my_strategy import MyStrategy

@pytest.fixture
def strategy(mock_vector_store):
    return MyStrategy(vector_store=mock_vector_store)

@pytest.mark.asyncio
async def test_retrieve_returns_results(strategy):
    results = await strategy.retrieve("test query", top_k=5)
    assert len(results) <= 5
    assert all(r.content for r in results)

@pytest.mark.asyncio
async def test_preprocess(strategy):
    processed = strategy._preprocess("test query")
    assert isinstance(processed, str)
```

### Step 4: Update Documentation

Add the new strategy to `GET /api/search-modes` by updating the mode list in the route handler, and document it in `docs/api-reference.md`.

---

## Adding a New Agent Tool

Agent tools extend the agentic orchestration layer with new capabilities.

### Step 1: Implement the Tool

```python
# services/gateway/gateway/agent/tools/my_tool.py
from gateway.agent.tools.base import AgentTool, ToolResult

class MyTool(AgentTool):
    name = "my_tool"
    description = "Describe what this tool does so the agent can decide when to use it."
    parameters = {
        "input": {"type": "string", "description": "The input to process"},
    }

    async def execute(self, input: str) -> ToolResult:
        # Perform the tool action
        output = f"Processed: {input}"
        return ToolResult(output=output, success=True)
```

### Step 2: Register the Tool

Add the tool to the registry in `services/gateway/gateway/agent/tools/__init__.py`:

```python
from gateway.agent.tools.my_tool import MyTool

TOOL_REGISTRY = {
    "rag_search": RagSearchTool,
    "data_api_lookup": DataApiLookupTool,
    "calculator": CalculatorTool,
    "my_tool": MyTool,  # Add here
}
```

### Step 3: Enable the Tool

Add the tool name to the `AGENT_TOOLS` environment variable:

```bash
AGENT_TOOLS=rag_search,data_api_lookup,my_tool
```

---

## Adding a New API Endpoint

### Gateway (FastAPI)

```python
# services/gateway/gateway/api/my_endpoint.py
from fastapi import APIRouter, Depends
from gateway.core.deps import get_current_user
from gateway.models.my_models import MyRequest, MyResponse

router = APIRouter(prefix="/api", tags=["my-feature"])

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(request: MyRequest, user=Depends(get_current_user)):
    # Implementation
    return MyResponse(result="done")
```

Register the router in `services/gateway/gateway/api/__init__.py`:

```python
from gateway.api.my_endpoint import router as my_router
app.include_router(my_router)
```

### Data API (Express)

```javascript
// services/data-api/src/routes/myRoute.js
const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');

router.get('/my-endpoint', auth, async (req, res, next) => {
  try {
    const data = await MyModel.find({});
    res.json({ data });
  } catch (err) {
    next(err);
  }
});

module.exports = router;
```

Register in `services/data-api/src/routes/index.js`:

```javascript
const myRoute = require('./myRoute');
app.use('/api', myRoute);
```

---

## Testing Guide

### Gateway Tests

```bash
cd services/gateway

# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=gateway --cov-report=html

# Run a specific test file
pytest tests/retrieval/test_vector_strategy.py

# Run tests matching a pattern
pytest -k "test_retrieve"
```

### Data API Tests

```bash
cd services/data-api

# Install dev dependencies
npm install

# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

### UI Tests

```bash
cd services/ui

# Run unit tests
npm test

# Run end-to-end tests
npm run test:e2e
```

### Integration Tests

Integration tests require running services. Use Docker Compose:

```bash
docker compose -f docker-compose.test.yml up -d
pytest tests/integration/ --timeout=60
docker compose -f docker-compose.test.yml down
```

---

## Debugging

### Gateway

**Enable debug logging:**

```bash
LOG_LEVEL=debug DEBUG=true docker compose up gateway
```

**Attach a debugger:**

```bash
# In docker-compose.override.yml
services:
  gateway:
    command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "5000"]
    ports:
      - "5678:5678"
```

Then attach VS Code with a "Remote Attach" launch configuration pointing to `localhost:5678`.

**Inspect retrieval results:**

Add `"options": {"debug": true}` to a `/api/inquire` request. The response will include a `debug` field with intermediate retrieval scores, reranking details, and the full prompt sent to the LLM.

### Data API

```bash
# Enable verbose logging
LOG_LEVEL=debug NODE_ENV=development npm start

# Use Node.js inspector
node --inspect=0.0.0.0:9229 src/index.js
```

### UI

```bash
# Start in development mode with hot reload
npm run dev

# React DevTools and browser console are the primary debugging tools
# The WebSocket client logs connection events to the console in dev mode
```

---

## Profiling

### Gateway Performance Profiling

**cProfile for synchronous code:**

```python
import cProfile
cProfile.run('sync_function()', 'output.prof')

# Visualize
pip install snakeviz
snakeviz output.prof
```

**py-spy for production profiling (no code changes required):**

```bash
pip install py-spy
py-spy top --pid $(pgrep -f uvicorn)

# Generate a flame graph
py-spy record -o flamegraph.svg --pid $(pgrep -f uvicorn) --duration 30
```

**Timing specific pipeline stages:**

The Gateway logs timing for each pipeline stage when `LOG_LEVEL=debug`:

```
DEBUG retrieval.vector: query_embedding_ms=12 search_ms=45 chunks_found=10
DEBUG reranking: model_load_ms=0 inference_ms=230 input_chunks=10 output_chunks=5
DEBUG generation: prompt_tokens=1842 ttft_ms=320 total_ms=2100
```

### Memory Profiling

```bash
pip install memray
memray run -o output.bin -m uvicorn gateway.main:app
memray flamegraph output.bin -o memory.html
```

Watch for:

- Embedding model loaded multiple times (should be a singleton)
- Reranker model not released after inference batch
- Large conversation histories held in memory instead of streamed from MongoDB

---

## Code Style and Linting

### Gateway (Python)

```bash
# Format
ruff format gateway/ tests/

# Lint
ruff check gateway/ tests/

# Type checking
mypy gateway/
```

### Data API and UI (JavaScript/TypeScript)

```bash
# Lint
npm run lint

# Format
npm run format

# Type checking (UI only)
npx tsc --noEmit
```

All checks run in CI via GitHub Actions. PRs must pass all checks before merge.
