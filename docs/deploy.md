# Deployment Guide

## Prerequisites

- VPS running Linux (Ubuntu recommended)
- Python 3.14
- Docker (for PostgreSQL)
- Git access to the repository

---

## 1. First-time Server Setup

### 1.1 Clone the repository

```bash
git clone <repo-url> /root/stock-filter
cd /root/stock-filter
```

### 1.2 Create virtual environment and install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 1.3 Create `.env` file

```bash
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_data
EOF
```

### 1.4 Start PostgreSQL with Docker

```bash
make db_start
```

This runs `postgres:latest` on port `5432` with:

- User: `postgres`
- Password: `password`
- Database: `stock_data`

### 1.5 Run database migrations

```bash
make migrate
```

### 1.6 Run the crawler to populate initial data

```bash
cd backend && python -B crawler/crawler.py
```

---

## 2. Systemd Service Setup

Create two systemd service files so the app survives reboots.

### 2.1 Backend service

```bash
cat > /etc/systemd/system/stock-filter-backend.service << 'EOF'
[Unit]
Description=Stock Filter Backend
After=network.target

[Service]
WorkingDirectory=/root/stock-filter/backend
ExecStart=/root/stock-filter/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
EnvironmentFile=/root/stock-filter/.env

[Install]
WantedBy=multi-user.target
EOF
```

### 2.2 Frontend service

```bash
cat > /etc/systemd/system/stock-filter-frontend.service << 'EOF'
[Unit]
Description=Stock Filter Frontend
After=network.target

[Service]
WorkingDirectory=/root/stock-filter/frontend
ExecStart=/root/stock-filter/.venv/bin/streamlit run app.py --server.port 8501
Restart=always
EnvironmentFile=/root/stock-filter/.env

[Install]
WantedBy=multi-user.target
EOF
```

### 2.3 Enable and start services

```bash
sudo systemctl daemon-reload
sudo systemctl enable stock-filter-backend stock-filter-frontend
sudo systemctl start stock-filter-backend stock-filter-frontend
```

---

## 3. Continuous Deployment (GitHub Actions)

CD is automated via `.github/workflows/deploy.yml`. On every push to `main`, GitHub Actions will:

1. SSH into the VPS
2. Pull latest code
3. Install new dependencies
4. Run `make migrate`
5. Restart both systemd services

### Required GitHub Secrets

| Secret        | Description                            |
| ------------- | -------------------------------------- |
| `VPS_HOST`    | IP or hostname of the VPS              |
| `VPS_USER`    | SSH username (e.g. `root`)             |
| `VPS_SSH_KEY` | Private SSH key with access to the VPS |

---

## 4. Manual Deployment

When automated CD is not available:

```bash
cd /root/stock-filter
source .venv/bin/activate
git pull origin main
pip install -r requirements.txt
make migrate
sudo systemctl restart stock-filter-backend stock-filter-frontend
```

---

## 5. Verify Deployment

```bash
# Check service status
sudo systemctl status stock-filter-backend
sudo systemctl status stock-filter-frontend

# Check backend is responding
curl http://localhost:8000/stocks

# Tail logs
journalctl -u stock-filter-backend -f
journalctl -u stock-filter-frontend -f
```

---

## 6. Useful Commands

| Command               | Description                          |
| --------------------- | ------------------------------------ |
| `make db_start`       | Start PostgreSQL container           |
| `make db_stop`        | Stop and remove PostgreSQL container |
| `make migrate`        | Run SQL migrations                   |
| `make remove_pycache` | Clean up `__pycache__` directories   |
