# EMA Crossover Bot - OpenAlgo Integration Guide

## Current Setup ✅

Your bot is located at: `/Users/tripti/Documents/ema_crossover_realtime_bot/ema_crossover_realtime.py`

**Configuration:**
- API Key: `d8f1f4fdc63658804ea34ec5a30161327970bd24d76d6e48c4a4ebc8fba5eaf0`
- API Host: `http://127.0.0.1:5050`
- Symbol: RELIANCE (NSE)
- Mode: Paper Trading
- Strategy: EMA Crossover (9/21)

## How to Run Your Bot

### Option 1: Run Standalone (Current Setup) ✅ **RECOMMENDED**

Your bot is already configured to run standalone and connect to OpenAlgo via API.

```bash
cd /Users/tripti/Documents/ema_crossover_realtime_bot
python ema_crossover_realtime.py
```

**Where to see activity:**
1. **API Logs**: http://127.0.0.1:5050/logs → Shows all API calls from your bot
2. **Orderbook**: http://127.0.0.1:5050/orderbook → Shows orders placed by your bot
3. **Positions**: http://127.0.0.1:5050/positions → Shows your open positions
4. **Bot Console**: Your terminal will show EMA calculations, signals, and trades

**Note:** The bot runs OUTSIDE Docker and connects via API - this is the correct setup for independent strategies.

---

### Option 2: Use OpenAlgo's Python Strategy Hosting

To run your bot INSIDE OpenAlgo and see it in the Python Strategy dashboard:

#### Step 1: Upload Strategy to OpenAlgo

```bash
# Copy your bot to the strategies/scripts folder
cp /Users/tripti/Documents/ema_crossover_realtime_bot/ema_crossover_realtime.py \\
   /Users/tripti/Documents/algotrading/openalgo/strategies/scripts/ema_crossover_realtime.py
```

#### Step 2: Access Python Strategy Manager

1. Login to OpenAlgo: http://127.0.0.1:5050/auth/login
2. Navigate to: http://127.0.0.1:5050/python

#### Step 3: Upload and Start

1. Click "Upload Strategy"
2. Select `ema_crossover_realtime.py`
3. Click "Start" to run it
4. View logs in real-time

**Benefits:**
- Automatic restart on failure
- Scheduled start/stop times
- Centralized logging
- Process isolation

---

## Understanding Analyzer Mode

**What Analyzer Mode Shows:**
- Sandbox/Paper trading positions created via OpenAlgo's sandbox API
- Test orders placed through OpenAlgo's `/api/v1/placeordersandbox` endpoint
- PnL tracking for sandbox positions

**What It Does NOT Show:**
- External bot activity (your bot connects via regular API, not sandbox)
- Real broker positions (unless you connect to a real broker)
- API call logs (use /logs for that)

---

## Troubleshooting

### Bot not placing orders?

Check:
1. Analyzer mode is enabled (already confirmed ✅)
2. API key is valid (test with: `curl -H "X-API-KEY: your-key" http://127.0.0.1:5050/api/v1/funds`)
3. Bot has WebSocket connection (should show LTP updates in console)
4. Market is open (check NSE trading hours: 9:15 AM - 3:30 PM IST)

### WebSocket connection issues?

Your bot uses WebSocket for real-time LTP. Ensure:
- OpenAlgo WebSocket proxy is running: `curl http://127.0.0.1:8765` (should fail but port is open)
- Health check shows WebSocket OK: `curl http://127.0.0.1:5050/api/health | jq '.checks.websocket'`

### Want to see paper trading in analyzer?

Use OpenAlgo's sandbox API in your bot:
```python
# Instead of:
client.placeorder(...)

# Use:
client.placeordersandbox(...)  # If available in openalgo SDK
```

Or modify your bot to use OpenAlgo's sandbox endpoints directly.

---

## Quick Start Commands

```bash
# 1. Start OpenAlgo (Docker)
cd /Users/tripti/Documents/algotrading/openalgo
docker-compose up -d

# 2. Verify services are healthy
curl http://127.0.0.1:5050/api/health | jq

# 3. Run your bot (in a new terminal)
cd /Users/tripti/Documents/ema_crossover_realtime_bot
python ema_crossover_realtime.py

# 4. Monitor activity
# - Open http://127.0.0.1:5050/logs in browser
# - Watch bot console output
```

---

## Next Steps

1. **Test the bot**: Run it and watch for EMA crossover signals
2. **Monitor API usage**: Check /logs to see all API calls
3. **Review trades**: Check /orderbook and /tradebook for executed orders
4. **Adjust parameters**: Modify .env in your bot folder to tune EMA periods, quantity, etc.

---

## Support

- OpenAlgo API Docs: http://127.0.0.1:5050/download
- Health Dashboard: http://127.0.0.1:5050/health
- Python Strategies: http://127.0.0.1:5050/python
- API Logs: http://127.0.0.1:5050/logs
