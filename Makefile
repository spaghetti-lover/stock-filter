.PHONY: remove_pycache db_start db_stop migrate migrate_prod migrate_rollback db_check frontend backend \
        up down build logs ps

remove_pycache:
	find . -type d -name "__pycache__" -exec rm -r {} +

db_start:
	docker run -d \
		--name stock_db \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD=password \
		-e POSTGRES_DB=stock_data \
		-p 5432:5432 \
		postgres:latest

db_stop:
	docker stop stock_db && docker rm stock_db

migrate:
	cd backend && uv run yoyo apply --no-config-file \
		--database "postgresql://postgres:password@localhost:5432/stock_data" \
		./db/migrations

migrate_prod:
	docker exec -i stock-backend \
		sh -c "python3 -B -m yoyo apply --no-config-file \
		--database 'postgresql://postgres:password@db:5432/stock_data' \
		./db/migrations"

migrate_rollback:
	cd backend && uv run yoyo rollback --no-config-file \
		--database "postgresql://postgres:password@localhost:5432/stock_data" \
		./db/migrations

db_check:
	psql "postgresql://postgres:password@localhost:5432/stock_data" -c "SELECT count(*) AS total_stocks FROM stock_metrics;" -c "SELECT symbol, exchange, price, gtgd20, crawled_at FROM stock_metrics LIMIT 10;" -c "SELECT * FROM crawl_log ORDER BY id DESC LIMIT 5;"

frontend:
	cd frontend && bun dev

frontend_install:
	cd frontend && bun install

frontend_build:
	cd frontend && bun run build

backend:
	cd backend && uv run uvicorn main:app

# Docker Compose (production)
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps
