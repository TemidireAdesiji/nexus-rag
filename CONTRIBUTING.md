# Contributing to NexusRAG

Thank you for your interest in contributing to NexusRAG. This document explains how to get started, our development workflow, and the standards we maintain across the codebase.

## Getting Started

1. Fork the repository and clone your fork locally.
2. Ensure you have the required toolchains installed:
   - Python 3.11+ with pip
   - Node.js 20+ with npm
   - Docker and Docker Compose
3. Set up each service for local development:

```bash
# Gateway (Python)
cd services/gateway
pip install -e ".[dev]"

# Data API (Node.js)
cd services/data-api
npm install

# UI (React)
cd services/ui
npm install
```

4. Copy the example environment files and fill in your configuration:

```bash
cp services/gateway/.env.example services/gateway/.env
cp services/data-api/.env.example services/data-api/.env
```

5. Start the infrastructure dependencies:

```bash
docker compose up mongodb redis -d
```

## Development Workflow

### Branching Strategy

- Branch from `main` for all work.
- Use descriptive branch names: `feat/add-bm25-retrieval`, `fix/session-timeout`, `docs/api-reference`.
- Keep branches focused on a single concern. If a change touches multiple services, that is fine, but it should address one logical change.

### Conventional Commits

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. Every commit message must use one of these prefixes:

- `feat:` -- a new feature or capability
- `fix:` -- a bug fix
- `docs:` -- documentation changes only
- `refactor:` -- code restructuring without behavior change
- `test:` -- adding or updating tests
- `chore:` -- build configuration, dependency updates, tooling
- `perf:` -- performance improvements

Examples:

```
feat: add BM25 keyword scoring to combined retrieval strategy
fix: prevent session store from exceeding max message limit
docs: add WebSocket protocol section to API reference
```

### Running the Full Stack Locally

```bash
# Start everything
docker compose up --build

# Or run services individually for faster iteration
cd services/gateway && python -m gateway.server
cd services/data-api && npm run dev
cd services/ui && npm run dev
```

## Running Tests

### Gateway (Python)

```bash
cd services/gateway
pytest                          # Run all tests
pytest --cov=gateway            # With coverage report
pytest tests/unit/              # Unit tests only
pytest tests/integration/       # Integration tests only
```

### Data API (Node.js)

```bash
cd services/data-api
npm test                        # Run all tests
npm run test:coverage           # With coverage report
```

### UI (React)

```bash
cd services/ui
npm test                        # Run test suite
```

All tests must pass before a pull request will be reviewed.

## Code Style

### Python (Gateway)

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
cd services/gateway
ruff check .                    # Lint
ruff format .                   # Format
mypy gateway/                   # Type checking
```

Configuration is in `pyproject.toml`. Key rules:

- Line length: 79 characters
- Target: Python 3.11
- Enabled rule sets: E, F, W, I, UP, B, SIM

### Node.js (Data API)

We use ESLint and Prettier:

```bash
cd services/data-api
npx eslint src/                 # Lint
npx prettier --write src/       # Format
```

### React (UI)

```bash
cd services/ui
npx eslint src/                 # Lint
npx prettier --write src/       # Format
```

### General Conventions

- Write docstrings for all public functions and classes (Python).
- Use JSDoc comments for exported functions (TypeScript).
- Prefer explicit types over `any`.
- Keep functions short and focused. If a function exceeds 40 lines, consider splitting it.
- Name things clearly. Avoid abbreviations unless they are universally understood (e.g., `id`, `url`, `http`).

## Pull Request Process

1. Ensure all tests pass and linters report no errors.
2. Update documentation if your change affects public APIs, configuration, or deployment procedures.
3. Write a clear PR description explaining what changed and why.
4. Link to any related issues.
5. Request review from at least one maintainer.
6. Address review feedback promptly. Use fixup commits during review, then squash before merge if requested.

### PR Title Format

Follow the same conventional commit format for PR titles:

```
feat: add support for PDF table extraction during ingestion
```

### What We Look For in Reviews

- Correctness: does the change do what it claims?
- Tests: are edge cases covered?
- Performance: does this introduce unnecessary overhead?
- Security: are inputs validated? Are secrets handled properly?
- Maintainability: will someone unfamiliar with this code understand it in six months?

## Reporting Issues

Use GitHub Issues to report bugs or request features. When filing a bug report, include:

1. **Environment**: OS, Python/Node version, Docker version, browser (if UI-related).
2. **Steps to reproduce**: minimal, concrete steps that trigger the issue.
3. **Expected behavior**: what should happen.
4. **Actual behavior**: what happens instead, including error messages and logs.
5. **Configuration**: relevant environment variables (redact secrets).

For feature requests, describe the use case and the problem you are trying to solve, not just the solution you have in mind.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold a welcoming and respectful environment.
