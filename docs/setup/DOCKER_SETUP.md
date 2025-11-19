# OpenAlgo Docker Setup Guide

This guide will help you set up and run OpenAlgo using Docker and Docker Compose.

## Prerequisites

- Docker Desktop installed (includes Docker and Docker Compose)
  - Download from: https://www.docker.com/products/docker-desktop/
- Minimum 4GB RAM available for Docker
- 2GB disk space

## Quick Start (5 minutes)

### 1. Configure Environment

Copy the sample environment file and configure it:

```bash
# Copy sample environment file
cp .sample.env .env
```

**IMPORTANT**: Edit `.env` and configure at least these required fields:

```bash
# Open .env in your text editor
nano .env  # or vi .env, or code .env
```

**Minimum required changes:**

1. **Set a secure APP_KEY** (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
2. **Set a secure API_KEY_PEPPER** (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
3. **Configure your broker**:
   ```bash
   REDIRECT_URL=http://127.0.0.1:5000/zerodha/callback  # Change 'zerodha' to your broker
   BROKER_API_KEY=your_actual_api_key
   BROKER_API_SECRET=your_actual_api_secret
   ```

### 2. Build and Start

```bash
# Build the Docker image and start the services
docker-compose up -d --build
```

The `-d` flag runs containers in the background (detached mode).

### 3. Verify It's Running

```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f openalgo
```

### 4. Access OpenAlgo

Open your browser and navigate to:

- **Web UI**: http://localhost:5000
- **WebSocket**: ws://localhost:8765
- **API Docs**: http://localhost:5000/api/v1/ (if available)

## Service Endpoints

### Web Interface
- **URL**: http://localhost:5000
- **Description**: Full web UI for managing trades, strategies, and monitoring

### REST API
- **Base URL**: http://localhost:5000/api/v1/
- **Authentication**: API Key (generate in Settings → API Keys after first login)

Key endpoints:
- `GET /api/v1/ping` - Health check
- `POST /api/v1/placeorder` - Place orders
- `GET /api/v1/positions` - Get positions
- `GET /api/v1/orderbook` - Get order book

### WebSocket Server
- **URL**: ws://localhost:8765
- **Description**: Real-time market data streaming
- **Usage**: For LTP updates, market depth, quotes

## Common Commands

### Start Services
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

### View Logs
```bash
# All logs
docker-compose logs -f

# Only OpenAlgo logs
docker-compose logs -f openalgo

# Last 100 lines
docker-compose logs --tail=100 openalgo
```

### Restart Services
```bash
docker-compose restart
```

### Rebuild After Code Changes
```bash
docker-compose down
docker-compose up -d --build
```

### Access Container Shell
```bash
docker-compose exec openalgo /bin/bash
```

### Check Resource Usage
```bash
docker stats openalgo-web
```

## Data Persistence

Your data is stored in:

- **Database**: Docker volume `openalgo_db` (persistent across restarts)
- **Logs**: `./log` directory (mounted from host)
- **Strategies**: `./strategies` directory (mounted from host)
- **Keys**: `./keys` directory (mounted from host)

To backup your data:
```bash
# Backup database
docker-compose exec openalgo cp -r /app/db /app/backup_db

# Copy to host
docker cp openalgo-web:/app/backup_db ./backup_db
```

## Port Configuration

Default ports (change in `.env` if needed):

- `FLASK_PORT=5000` - Web UI and API
- `WEBSOCKET_PORT=8765` - WebSocket server

Example: To run on different ports:
```bash
# In .env file
FLASK_PORT=8080
WEBSOCKET_PORT=9000
```

Then restart:
```bash
docker-compose down && docker-compose up -d
```

## Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker-compose logs openalgo

# Common issues:
# 1. Port already in use - change FLASK_PORT in .env
# 2. Missing .env file - copy from .sample.env
# 3. Invalid broker configuration - check REDIRECT_URL and API keys
```

### Can't connect to broker
```bash
# 1. Verify your broker credentials in .env
# 2. Check broker is in VALID_BROKERS list
# 3. Ensure REDIRECT_URL matches your broker callback
# 4. Check container logs for auth errors
docker-compose logs -f openalgo | grep -i error
```

### Database errors
```bash
# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d --build
```

### WebSocket connection issues
```bash
# Verify WebSocket is running
docker-compose exec openalgo ps aux | grep websocket

# Check WebSocket logs
docker-compose logs openalgo | grep -i websocket
```

## Development Mode

For local development with hot-reload:

1. Edit `.env`:
   ```bash
   FLASK_ENV=development
   FLASK_DEBUG=True
   ```

2. Restart:
   ```bash
   docker-compose down && docker-compose up -d
   ```

3. Code changes will require rebuild:
   ```bash
   docker-compose up -d --build
   ```

## API Usage Example

After logging in and generating an API key:

```bash
# Health check
curl http://localhost:5000/api/v1/ping

# Place order (example)
curl -X POST http://localhost:5000/api/v1/placeorder \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -d '{
    "symbol": "RELIANCE",
    "exchange": "NSE",
    "action": "BUY",
    "quantity": 1,
    "price": 2500,
    "product": "MIS",
    "order_type": "LIMIT"
  }'
```

## WebSocket Usage Example

```python
import websocket
import json

def on_message(ws, message):
    print(f"Received: {message}")

def on_open(ws):
    # Subscribe to LTP updates
    subscribe_msg = {
        "action": "subscribe",
        "symbols": ["NSE:RELIANCE"]
    }
    ws.send(json.dumps(subscribe_msg))

ws = websocket.WebSocketApp(
    "ws://localhost:8765",
    on_message=on_message,
    on_open=on_open
)

ws.run_forever()
```

## Clean Uninstall

To completely remove OpenAlgo and all data:

```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker rmi openalgo:latest

# Remove local directories (optional)
rm -rf ./log ./strategies ./keys
```

## Next Steps

1. **First Login**: Navigate to http://localhost:5000 and complete initial setup
2. **Configure Broker**: Connect your broker account via the web UI
3. **Generate API Key**: Settings → API Keys → Generate new key
4. **Explore Features**:
   - Order placement and management
   - Strategy deployment
   - Real-time monitoring
   - Chartink integration
   - Telegram bot (if configured)

## Support

- Documentation: https://docs.openalgo.in
- Discord: https://discord.com/invite/UPh7QPsNhP
- GitHub Issues: https://github.com/marketcalls/openalgo

## Security Reminders

- ✅ Always use strong random values for `APP_KEY` and `API_KEY_PEPPER`
- ✅ Keep your `.env` file secure and never commit it to version control
- ✅ Use HTTPS in production (set `HOST_SERVER` to your HTTPS domain)
- ✅ Regularly update OpenAlgo (`docker-compose pull && docker-compose up -d`)
- ✅ Monitor logs for suspicious activity
- ✅ Use strong passwords for broker accounts and OpenAlgo login
