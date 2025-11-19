## Quick orientation — what this repo is

- OpenAlgo is a Flask-based web application (Python >= 3.12) that exposes a unified REST API (`/api/v1/*`), a web UI, and real-time streams via Socket.IO and a separate WebSocket proxy (port 8765).
- Major runtime pieces:
  - WSGI app: `app.py` (creates Flask app, registers blueprints and RESTx API `restx_api.api_v1_bp`).
  - WebSocket proxy: launched from `websocket_proxy.server` (the proxy runs separately on port 8765 and bridges brokers -> ZMQ -> clients).
  - Socket.IO config: `extensions.py` (SocketIO instance with `async_mode='threading'` — see notes below about eventlet).
  - Broker adapters live under `broker/` and follow a common pattern: `auth_api.py`, `order_api.py`, `data.py`, `transform_data.py`, and `broker_adapter.py`.

## Big-picture architecture and data flows (short)

- Brokers -> broker adapters -> publish to ZMQ message bus. The WebSocket proxy subscribes to ZMQ and forwards to clients.
- REST requests hit Flask blueprints (`blueprints/`) and the `restx_api` blueprint for `/api/v1/*` routes.
- Important startup/initialization tasks are performed in `app.setup_environment()` (parallel DB init) and a few services (execution engine, squareoff scheduler) auto-start when analyzer mode is enabled.

## Important files to reference

- `app.py` — entrypoint: blueprint registration, CSRF, CORS, limiter, middleware, DB init and service auto-start.
- `extensions.py` — SocketIO options used across the app.
- `websocket_proxy/` — WebSocket proxy module (executed separately in `start.sh`).
- `broker/` — broker adapters and adapters' common patterns.
- `database/` — DB init helpers and models; `setup_environment()` initializes these in parallel.
- `pyproject.toml` / `requirements.txt` — pinned dependencies (Python >= 3.12).
- `start.sh` and `Dockerfile` — canonical production startup sequence.

## Developer workflows (concrete commands)

- Quick local dev (recommended):

  1. Create a venv and install deps:

     python -m venv .venv
     . .venv/bin/activate
     pip install -r requirements.txt

  2. Export minimal env vars (example):
     export APP_KEY="<random-secret>"
     export DATABASE_URL="sqlite:///db/openalgo.db"  # or a real DB URL
     export HOST_SERVER="http://127.0.0.1:5000"

  3. Start the WebSocket proxy and the app (the project expects the proxy to be available):

     # starts ZMQ -> ws proxy
     python -m websocket_proxy.server &

     # start the app using the same command as production (Gunicorn + eventlet)
     gunicorn --worker-class eventlet --workers 1 --bind 0.0.0.0:5000 app:app

- Production (containerized): `./start.sh` inside the Docker image is the canonical startup script. It launches the websocket proxy and then runs gunicorn with eventlet (see `Dockerfile`). Use `docker-compose.yaml` / provided Dockerfile.

## Key project-specific conventions & gotchas for an AI coding assistant

- Blueprints are central. To add endpoints, add a blueprint under `blueprints/` and register it in `app.py` (search for the block of `app.register_blueprint(...)`).
- Broker integrations follow a strict file-per-concern layout (auth/order/data/transform). When generating broker code follow these filenames and function shapes.
- Socket.IO: `extensions.socketio` is created with `async_mode='threading'`. Historically the project commented about greenlet issues; production uses eventlet in the container. If you change async mode, verify eventlet/greenlet compatibility and container behavior. Prefer matching production (eventlet) for real-time features unless debugging concurrency issues.
- WebSocket proxy must be running for real-time streaming tests; many features depend on it (LTP / depth / ticker).
- DB initialization runs in parallel in `app.setup_environment()`; follow existing helpers in `database/` when adding new DB tables (add `init_db`/`init_latency_db` style function and include it in the initializer list).

## Integration points to watch for when changing behavior

- Authentication & API keys: `blueprints/apikey.py` and `database/token_db*.py` — changes here affect MCP clients and API usage.
- Rate-limiting is env-controlled (see README and `limiter.py`), so document new endpoints' rate impact and add env config if needed.
- MCP integration lives under `mcp/` — if adding AI-enabled features ensure the MCP tools stay consistent with existing MCP endpoints.

## Tests & local validation

- Tests are under `test/` — run `pytest -q` after installing `pytest` from `requirements.txt`.
- Quick runtime smoke test: start websocket proxy + gunicorn (above) and curl `/api/v1/ping` (or hit web UI) to verify server & proxy are reachable.

## When you need more context or permission

- If you need to add or change long-running services (execution engine, scheduler), prefer adding a feature branch and include a small integration test or a manual run script under `scripts/` / `start.sh`.

---
If you'd like, I can iterate this file to include more examples (e.g., a sample env file, common debug logs to watch in `log/`, or a minimal unit test template for a blueprint). What additional details would help you most? 
