# Local

## Frontend

```
make frontend
```

## Backend

```
make backend
```

# Server

```
git clone
```

```
git pull
```

- Add .env

```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
OPENAI_API_KEY=sk-proj-...
DATABASE_URL=postgresql://postgres:password@db-stock-data:5432/stock_data
```

```
docker-compose up -d --build
```

```
docker compose exec backend sh
```

```
apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/
```

```
curl -fsSL https://claude.ai/install.sh | bash
```

```
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && . ~/.bashrc
```

- Login Claude

```
make migrate_prod
```
