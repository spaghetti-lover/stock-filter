.PHONY: remove_pycache db_start db_stop migrate db_check frontend backend

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
	psql "postgresql://postgres:password@localhost:5432/stock_data" -f backend/db/migrations/001_create_stocks.sql

db_check:
	psql "postgresql://postgres:password@localhost:5432/stock_data" -c "SELECT count(*) AS total_stocks FROM stock_metrics;" -c "SELECT symbol, exchange, price, gtgd20, crawled_at FROM stock_metrics LIMIT 10;" -c "SELECT * FROM crawl_log ORDER BY id DESC LIMIT 5;"

frontend:
	cd frontend && uv run streamlit run app.py --server.headless true

backend:
	cd backend && uv run uvicorn main:app