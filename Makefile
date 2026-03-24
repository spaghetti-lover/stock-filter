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