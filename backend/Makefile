.PHONY: help dev test lint type migrate revision db.reset install clean

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

help: ## Show available commands
	@echo "$(GREEN)ArbitrageVault Backend Commands$(NC)"
	@echo "================================="
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(YELLOW)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies with uv
	@echo "$(GREEN)Installing dependencies...$(NC)"
	uv sync

dev: ## Start development server with hot reload
	@echo "$(GREEN)Starting development environment...$(NC)"
	@make --no-print-directory ensure-db
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

ensure-db: ## Ensure PostgreSQL is running
	@echo "$(GREEN)Ensuring PostgreSQL is running...$(NC)"
	@docker-compose -f docker-compose.dev.yml up -d postgres
	@echo "Waiting for PostgreSQL to be ready..."
	@for i in $$(seq 1 30); do \
		if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U memex > /dev/null 2>&1; then \
			echo "$(GREEN)PostgreSQL is ready!$(NC)"; \
			break; \
		fi; \
		echo "Waiting for PostgreSQL... ($$i/30)"; \
		sleep 2; \
	done

migrate: ## Run database migrations
	@echo "$(GREEN)Running migrations...$(NC)"
	@make --no-print-directory ensure-db
	uv run alembic upgrade head

revision: ## Create new migration (usage: make revision msg="description")
	@echo "$(GREEN)Creating migration: $(msg)$(NC)"
	uv run alembic revision --autogenerate -m "$(msg)"

db.reset: ## Reset database (DROP/CREATE/MIGRATE) - DEV ONLY
	@echo "$(YELLOW)WARNING: This will destroy all data!$(NC)"
	@echo "Press Ctrl+C to cancel, Enter to continue..."
	@read
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.dev.yml up -d postgres
	@make --no-print-directory ensure-db
	uv run alembic upgrade head
	@echo "$(GREEN)Database reset complete$(NC)"

test: ## Run all tests with coverage
	@echo "$(GREEN)Running tests...$(NC)"
	@make --no-print-directory ensure-db
	uv run coverage run -m pytest -v
	uv run coverage report
	uv run coverage html

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	@make --no-print-directory ensure-db
	uv run pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	@echo "$(GREEN)Running E2E tests...$(NC)"
	@make --no-print-directory ensure-db
	uv run pytest tests/e2e/ -v

lint: ## Run linting checks
	@echo "$(GREEN)Running lint checks...$(NC)"
	uv run ruff check .
	uv run black --check .

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	uv run ruff check . --fix
	uv run black .

type: ## Run type checking
	@echo "$(GREEN)Running type checks...$(NC)"
	uv run mypy app/

clean: ## Clean up temporary files
	@echo "$(GREEN)Cleaning up...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

docker-down: ## Stop all services
	@echo "$(GREEN)Stopping services...$(NC)"
	docker-compose -f docker-compose.dev.yml down