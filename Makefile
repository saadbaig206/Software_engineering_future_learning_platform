.PHONY: help install dev test lint migrate up down clean

help:
	@echo "FutureLearning Learning Engine — Developer Automation"
	@echo "Commands:"
	@echo "  install    Install backend and frontend dependencies"
	@echo "  dev        Run local development servers"
	@echo "  test       Execute backend and frontend test suites"
	@echo "  lint       Run linters (Ruff and ESLint)"
	@echo "  migrate    Apply Django migrations to Neon PostgreSQL"
	@echo "  up         Start full Docker Compose environment"
	@echo "  down       Stop Docker Compose environment"
	@echo "  clean      Remove cache files, build artifacts and containers"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev-backend:
	cd backend && python manage.py runserver

dev-frontend:
	cd frontend && npm run dev

dev-celery:
	cd backend && celery -A config worker --loglevel=info -Q default,media,adaptive,analytics,notifications

dev-beat:
	cd backend && celery -A config beat --loglevel=info

test-backend:
	cd backend && pytest --verbose

test-frontend:
	cd frontend && npm test

test: test-backend test-frontend

lint-backend:
	cd backend && ruff check .

lint-frontend:
	cd frontend && npm run lint

lint: lint-backend lint-frontend

migrate:
	cd backend && python manage.py migrate

makemigrations:
	cd backend && python manage.py makemigrations

up:
	docker compose -f infra/docker-compose.yml up -d --build

down:
	docker compose -f infra/docker-compose.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf frontend/.next frontend/dist
