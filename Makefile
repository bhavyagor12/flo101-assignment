# flo101 — common commands.
# All targets assume Docker + docker compose v2 are installed.

SHELL := /bin/bash
COMPOSE := docker compose
COMPOSE_DEV := docker compose -f docker-compose.yml -f docker-compose.dev.yml

.DEFAULT_GOAL := help

.PHONY: help setup up down dev logs build rebuild type-gen test eval demo-seed lint type-check clean nuke env-check

help: ## show this help
	@awk 'BEGIN{FS=":.*##"; printf "\nUsage: make \033[36m<target>\033[0m\n\nTargets:\n"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

env-check: ## verify .env exists
	@test -f .env || { echo "✗ .env missing — copy .env.example to .env and fill keys"; exit 1; }
	@echo "✓ .env present"

setup: env-check ## one-shot: install deps, build images, start services, seed
	@echo "▸ installing JS deps"
	pnpm install
	@echo "▸ building images"
	$(COMPOSE) build
	@echo "▸ starting services"
	$(COMPOSE) up -d
	@echo "▸ waiting for api healthcheck"
	@for i in $$(seq 1 30); do \
		if curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then \
			echo "✓ api healthy"; break; \
		fi; sleep 1; \
	done
	@echo ""
	@echo "✓ ready"
	@echo "  · API:  http://localhost:8000/docs"
	@echo "  · Web:  http://localhost:3000"

up: env-check ## start services in background
	$(COMPOSE) up -d

down: ## stop services
	$(COMPOSE) down

dev: env-check ## hot-reload api + web
	$(COMPOSE_DEV) up

logs: ## tail logs
	$(COMPOSE) logs -f

build: ## build images
	$(COMPOSE) build

rebuild: ## rebuild images without cache
	$(COMPOSE) build --no-cache

type-gen: ## Pydantic -> JSON Schema -> TS
	$(COMPOSE) exec -T api uv run python -m flo101_api.scripts.export_schema
	pnpm --filter @flo101/api-types run build

test: ## run all tests across the monorepo
	turbo run test

eval: ## run eval harness against goldens
	$(COMPOSE) exec -T api uv run pytest evals/ -v

demo-seed: ## populate 3 seed skill specs + corpora
	$(COMPOSE) exec -T api uv run python -m flo101_api.scripts.seed

lint: ## lint everything
	turbo run lint

type-check: ## strict type-check (pyright + tsc)
	turbo run type-check

clean: ## stop services, remove containers
	$(COMPOSE) down

nuke: ## stop services, remove containers AND volumes (DANGEROUS)
	$(COMPOSE) down -v
	rm -rf node_modules .turbo apps/*/node_modules apps/api/.venv
