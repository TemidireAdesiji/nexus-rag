.PHONY: help venv install run clean \
       docker-build docker-push docker-up docker-down docker-logs \
       test lint format \
       deploy-aws deploy-oci \
       deploy-aws-canary deploy-oci-canary \
       deploy-aws-bluegreen deploy-oci-bluegreen \
       smoke-test

SHELL := /bin/bash
OWNER ?= $(shell git remote get-url origin 2>/dev/null | sed -n 's|.*github.com[:/]\([^/]*\)/.*|\1|p')
TAG   ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo "latest")
REGISTRY := ghcr.io/$(OWNER)

# ──────────────────────────────────────────────
# General
# ──────────────────────────────────────────────

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'

venv: ## Create Python virtualenv for gateway
	python3 -m venv services/gateway/.venv
	@echo "Activate with: source services/gateway/.venv/bin/activate"

install: ## Install all service dependencies
	cd services/gateway && pip install -r requirements.txt
	cd services/data-api && npm ci
	cd services/ui && npm ci

run: ## Run all services locally (requires tmux or separate terminals)
	@echo "Starting MongoDB and Redis via Docker..."
	docker compose up -d mongodb redis
	@echo "Start each service in a separate terminal:"
	@echo "  cd services/data-api && npm run dev"
	@echo "  cd services/gateway && python -m gateway.main"
	@echo "  cd services/ui && npm run dev"

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name dist -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name build -exec rm -rf {} + 2>/dev/null || true
	rm -rf services/gateway/.venv

# ──────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────

docker-build: ## Build all Docker images
	docker build -t $(REGISTRY)/nexus-rag-gateway:$(TAG) services/gateway
	docker build -t $(REGISTRY)/nexus-rag-data-api:$(TAG) services/data-api
	docker build -t $(REGISTRY)/nexus-rag-ui:$(TAG) services/ui

docker-push: ## Push all Docker images to GHCR
	docker push $(REGISTRY)/nexus-rag-gateway:$(TAG)
	docker push $(REGISTRY)/nexus-rag-data-api:$(TAG)
	docker push $(REGISTRY)/nexus-rag-ui:$(TAG)

docker-up: ## Start full stack with docker compose
	docker compose up -d --build

docker-down: ## Stop and remove containers
	docker compose down -v

docker-logs: ## Tail logs from all containers
	docker compose logs -f

# ──────────────────────────────────────────────
# Testing & Quality
# ──────────────────────────────────────────────

test: ## Run all tests
	cd services/gateway && python -m pytest tests/ -v --tb=short
	cd services/data-api && npm test

lint: ## Run linters across all services
	cd services/gateway && ruff check .
	cd services/data-api && npx eslint src/
	cd services/ui && npx eslint src/

format: ## Auto-format code
	cd services/gateway && ruff format .
	cd services/data-api && npx prettier --write "src/**/*.ts"
	cd services/ui && npx prettier --write "src/**/*.{ts,tsx}"

# ──────────────────────────────────────────────
# Deployment - Rolling
# ──────────────────────────────────────────────

deploy-aws: ## Deploy to AWS EKS (rolling update)
	./deploy/scripts/rollout.sh rolling aws apply

deploy-oci: ## Deploy to OCI OKE (rolling update)
	./deploy/scripts/rollout.sh rolling oci apply

# ──────────────────────────────────────────────
# Deployment - Canary
# ──────────────────────────────────────────────

deploy-aws-canary: ## Deploy to AWS EKS (canary strategy)
	./deploy/scripts/rollout.sh canary aws apply

deploy-oci-canary: ## Deploy to OCI OKE (canary strategy)
	./deploy/scripts/rollout.sh canary oci apply

# ──────────────────────────────────────────────
# Deployment - Blue/Green
# ──────────────────────────────────────────────

deploy-aws-bluegreen: ## Deploy to AWS EKS (blue/green strategy)
	./deploy/scripts/rollout.sh bluegreen aws apply

deploy-oci-bluegreen: ## Deploy to OCI OKE (blue/green strategy)
	./deploy/scripts/rollout.sh bluegreen oci apply

# ──────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────

smoke-test: ## Run post-deploy smoke tests
	./deploy/scripts/smoke-test.sh
