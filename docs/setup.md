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

- Add .env (backend, root folder)
  - backend:
    ```
    VNSTOCK_API_KEY=
    DATABASE_URL=
    GOOGLE_API_KEY=
    # Trading-agent LLM providers
    OPENAI_API_KEY=
    ANTHROPIC_API_KEY=
    XAI_API_KEY=
    DEEPSEEK_API_KEY=
    DASHSCOPE_API_KEY=
    ZHIPU_API_KEY=
    OPENROUTER_API_KEY=

    ```
  - root:
    ```
    NEXT_PUBLIC_BACKEND_URL=http://194.34.232.128:8000
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
make migrate
```
