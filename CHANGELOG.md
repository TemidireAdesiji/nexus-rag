# Changelog

All notable changes to NexusRAG are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-01

### Added

- **Gateway service** (Python/FastAPI) providing the core RAG engine with retrieval, generation, and agentic orchestration.
- **Four retrieval strategies**: vector similarity search, combined vector+keyword hybrid search, multi-query expansion search, and query decomposition search.
- **Cross-encoder reranking** using `cross-encoder/ms-marco-MiniLM-L-6-v2` to reorder retrieved documents by relevance.
- **Agentic tool orchestration** with automatic planning, execution, and trace logging for structured data queries.
- **Tool registry** with auto-registration from the Data API client, supporting team, portfolio, vertical, and engagement queries.
- **OpenAI-compatible chat completion endpoint** at `/api/inquire/completions` for integration with existing toolchains.
- **WebSocket streaming** at `/ws/chat` delivering answers in configurable chunks with `thinking`, `status`, `chunk`, `complete`, and `error` event types.
- **Document ingestion pipeline** supporting PDF, DOCX, TXT, and Markdown files with configurable chunk size and overlap.
- **Session management** with in-memory session store, conversation history tracking, and configurable message limits.
- **Query result caching** with LRU eviction and configurable capacity.
- **Rate limiting** with per-minute request caps and Redis-backed counters.
- **Bearer token authentication** with optional enforcement on all Gateway endpoints.
- **Health, liveness, and readiness probes** at `/health`, `/alive`, and `/ready`.
- **Platform introspection endpoints** at `/api/platform/info` and `/api/platform/tools`.
- **Data API service** (Node.js/Express/MongoDB) providing REST endpoints for team members, portfolio investments, sectors, consultations, and document corpus management.
- **Data API authentication** with bearer token validation and credential endpoint.
- **Swagger/OpenAPI documentation** auto-generated and served at `/docs` on the Data API.
- **Data API seed data** for development and testing with realistic business records.
- **UI service** (React/Vite/Material UI) with a conversational chat interface.
- **Session sidebar** for managing multiple conversation sessions.
- **Strategy picker** allowing users to select retrieval strategies per query.
- **Source citation cards** displaying retrieved document excerpts with metadata.
- **System panel** showing platform health, configuration, and available tools.
- **Markdown rendering** for assistant responses with syntax highlighting.
- **Error boundary** component for graceful failure handling in the UI.
- **Docker Compose** configuration for local development with MongoDB, Redis, and all three services.
- **Kubernetes manifests** using Kustomize with base configuration, ConfigMap, Secrets, and Deployment resources.
- **Dockerfiles** for all three services with multi-stage builds.
- **Pydantic-based configuration** with environment variable parsing and validation for the Gateway.
- **Zod-based configuration** with environment variable validation for the Data API.
- **Structured logging** with Loguru (Gateway) and custom logger (Data API).
- **Request ID middleware** for distributed tracing correlation across both services.
- **CORS middleware** with configurable origins on both Gateway and Data API.
- **Comprehensive test suites** with unit and integration tests for the Gateway, and route tests for the Data API.
