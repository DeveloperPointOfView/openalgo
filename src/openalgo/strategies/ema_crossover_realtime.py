# 🔁 OpenAlgo Python Bot is running.
"""
Real-time EMA Crossover Strategy using OpenAlgo (Playground / Paper Mode)
- Uses OpenAlgo REST + WebSocket for live LTP updates
- Computes EMA using OpenAlgo's ta.ema
- Refreshes historical bars periodically (APScheduler, IST)
- Places MARKET orders on crossovers using OpenAlgo's placeorder
- Auto square-off at 15:20 IST (end of day)
- Generates Daily Trade Report with PnL at 15:25 IST and saves as CSV

Prerequisites
- openalgo installed and OpenAlgo app running in Playground/Test mode
- Set OPENALGO_API_KEY and OPENALGO_API_HOST in environment or .env
- pip install openalgo pandas apscheduler python-dotenv pytz

Notes
- This version is for paper trading/testing only (no real money)
- Prints quotes/LTP updates immediately as required.
- It does NOT write logs or DB entries unless you ask for it.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from threading import Event

import pandas as pd
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from dotenv import load_dotenv

from openalgo import api, ta

# -----------------------------
# Configuration
# -----------------------------
load_dotenv()
API_KEY = os.getenv("OPENALGO_API_KEY", "your-openalgo-apikey")
API_HOST = os.getenv("OPENALGO_API_HOST", "http://127.0.0.1:5000")
SYMBOL = os.getenv("SYMBOL", "RELIANCE")
EXCHANGE = os.getenv("EXCHANGE", "NSE")
INTERVAL = os.getenv("INTERVAL", "1m")
SHORT_EMA = int(os.getenv("SHORT_EMA", "9"))
LONG_EMA = int(os.getenv("LONG_EMA", "21"))
QUANTITY = int(os.getenv("QUANTITY", "1"))
PRODUCT = os.getenv("PRODUCT", "MIS")
STRATEGY_NAME = os.getenv("STRATEGY_NAME", "EMA_Crossover_Test")
HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", "3"))
REFRESH_SECONDS = int(os.getenv("REFRESH_SECONDS", "30"))
TIMEZONE = pytz.timezone("Asia/Kolkata")  # IST

# Paper Trading Configuration
TRADING_MODE = os.getenv("TRADING_MODE", "paper").lower()  # 'paper' or 'live'
PAPER_TRADING_ENABLED = os.getenv("PAPER_TRADING_ENABLED", "true").lower() == "true"
PAPER_TRADING_CAPITAL = float(os.getenv("PAPER_TRADING_CAPITAL", "100000"))  # Starting capital for paper trading

# API Rate Limiting Configuration
MAX_REQUESTS_PER_SECOND = int(os.getenv("MAX_REQUESTS_PER_SECOND", "3"))  # Kite Connect limit
MAX_ORDERS_PER_DAY = int(os.getenv("MAX_ORDERS_PER_DAY", "2000"))  # Zerodha order limit
MAX_API_REQUESTS_PER_DAY = int(os.getenv("MAX_API_REQUESTS_PER_DAY", "500"))
API_WARNING_THRESHOLD = int(os.getenv("API_WARNING_THRESHOLD", "450"))

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("ema_crossover_playground")

# -----------------------------
# State
# -----------------------------
client = api(api_key=API_KEY, host=API_HOST)
bar_df = pd.DataFrame()
last_signal = 0
trade_log = []  # store executed trades for reporting
running = True
stop_event = Event()
last_ltp = None  # track latest price for PnL

# Paper Trading State
paper_position = 0  # Current position: positive=long, negative=short, 0=flat
paper_capital = PAPER_TRADING_CAPITAL  # Available capital
paper_entry_price = 0.0  # Entry price for current position
paper_trades = []  # Paper trading trade history

# API Rate Limiting State
api_request_count = 0  # Track API requests made today
api_request_log = []  # Log of API requests with timestamps
last_reset_date = datetime.now(TIMEZONE).date()  # Track when to reset counter
order_count = 0  # Track orders placed today
request_timestamps = []  # Track request timestamps for per-second rate limiting

# -----------------------------
# Utility functions
# -----------------------------

def enforce_rate_limit():
    """
    Enforce Kite Connect's 3 requests per second limit.
    Sleeps if necessary to ensure we don't exceed the limit.
    """
    global request_timestamps
    
    current_time = time.time()
    
    # Remove timestamps older than 1 second
    request_timestamps = [ts for ts in request_timestamps if current_time - ts < 1.0]
    
    # If we've made 3 requests in the last second, wait
    if len(request_timestamps) >= MAX_REQUESTS_PER_SECOND:
        oldest_request = min(request_timestamps)
        sleep_time = 1.0 - (current_time - oldest_request)
        if sleep_time > 0:
            logger.debug(f"⏸️  Rate limit: sleeping {sleep_time:.3f}s to stay under {MAX_REQUESTS_PER_SECOND} req/sec")
            time.sleep(sleep_time)
            current_time = time.time()
            # Clean up old timestamps again after sleeping
            request_timestamps = [ts for ts in request_timestamps if current_time - ts < 1.0]
    
    # Record this request
    request_timestamps.append(current_time)


def check_api_limit():
    """Check if API request limit has been reached. Reset counter daily."""
    global api_request_count, last_reset_date, api_request_log, order_count
    
    current_date = datetime.now(TIMEZONE).date()
    
    # Reset counter if it's a new day
    if current_date > last_reset_date:
        logger.info(f"🔄 New day detected. Resetting counters.")
        logger.info(f"   Previous API requests: {api_request_count}")
        logger.info(f"   Previous orders: {order_count}")
        api_request_count = 0
        order_count = 0
        api_request_log = []
        last_reset_date = current_date
    
    # Check if daily limit reached
    if api_request_count >= MAX_API_REQUESTS_PER_DAY:
        logger.error(f"🚫 DAILY API LIMIT REACHED! {api_request_count}/{MAX_API_REQUESTS_PER_DAY} requests used today")
        return False
    
    # Warning threshold
    if api_request_count >= API_WARNING_THRESHOLD:
        logger.warning(f"⚠️  API LIMIT WARNING! {api_request_count}/{MAX_API_REQUESTS_PER_DAY} requests used ({int((api_request_count/MAX_API_REQUESTS_PER_DAY)*100)}%)")
    
    return True


def check_order_limit():
    """Check if daily order limit has been reached."""
    global order_count
    
    if order_count >= MAX_ORDERS_PER_DAY:
        logger.error(f"🚫 DAILY ORDER LIMIT REACHED! {order_count}/{MAX_ORDERS_PER_DAY} orders placed today")
        return False
    
    # Warning at 90% of order limit
    order_warning_threshold = int(MAX_ORDERS_PER_DAY * 0.9)
    if order_count >= order_warning_threshold:
        logger.warning(f"⚠️  ORDER LIMIT WARNING! {order_count}/{MAX_ORDERS_PER_DAY} orders placed ({int((order_count/MAX_ORDERS_PER_DAY)*100)}%)")
    
    return True


def log_api_request(endpoint: str):
    """Log an API request for tracking."""
    global api_request_count, api_request_log
    
    api_request_count += 1
    api_request_log.append({
        'timestamp': datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'),
        'endpoint': endpoint,
        'count': api_request_count
    })
    
    # Log every 25 requests (less frequent to reduce noise)
    if api_request_count % 25 == 0:
        logger.info(f"📊 API Usage: {api_request_count}/{MAX_API_REQUESTS_PER_DAY} requests ({int((api_request_count/MAX_API_REQUESTS_PER_DAY)*100)}%)")


def log_order(action: str):
    """Log an order for daily tracking."""
    global order_count
    order_count += 1
    
    if order_count % 10 == 0:
        logger.info(f"📊 Orders Today: {order_count}/{MAX_ORDERS_PER_DAY}")


def fetch_history(symbol: str, exchange: str, interval: str, days: int) -> pd.DataFrame:
    # Check API limit before making request
    if not check_api_limit():
        logger.error("Cannot fetch history - API limit reached for today")
        return pd.DataFrame()  # Return empty DataFrame
    
    # Enforce Kite Connect's 3 requests/second limit
    enforce_rate_limit()
    
    end_dt = datetime.now(TIMEZONE)
    start_dt = end_dt - timedelta(days=days)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")
    logger.info(f"Fetching history {symbol} {interval} from {start_date} to {end_date}")
    
    try:
        # Log API request
        log_api_request("history")
        
        result = client.history(
            symbol=symbol,
            exchange=exchange,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
        )
        
        # Check if result is an error dict instead of DataFrame
        if isinstance(result, dict):
            if 'error' in result or 'message' in result:
                logger.error(f"API Error: {result}")
                return pd.DataFrame()  # Return empty DataFrame
            # If dict but not error, try to convert to DataFrame
            try:
                df = pd.DataFrame(result)
            except Exception as e:
                logger.error(f"Failed to convert dict to DataFrame: {e}")
                return pd.DataFrame()
        else:
            df = result
            
        # Handle empty DataFrame
        if df.empty:
            logger.warning("Received empty historical data")
            return df
            
        # Fix index if it's not DatetimeIndex
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if df.index.tzinfo is None or df.index.tz is None:
            df.index = df.index.tz_localize(TIMEZONE)
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch history: {e}")
        return pd.DataFrame()


def compute_emas(df: pd.DataFrame, short_period: int, long_period: int) -> pd.DataFrame:
    df = df.copy()
    df[f"EMA_{short_period}"] = ta.ema(df["close"], short_period)
    df[f"EMA_{long_period}"] = ta.ema(df["close"], long_period)
    return df


def detect_signal(df: pd.DataFrame, short_period: int, long_period: int):
    if len(df) < max(short_period, long_period) + 2:
        return 0
    s_col = f"EMA_{short_period}"
    l_col = f"EMA_{long_period}"
    last_two = df[[s_col, l_col]].dropna().tail(2)
    if len(last_two) < 2:
        return 0
    prev_short, prev_long = last_two.iloc[0][s_col], last_two.iloc[0][l_col]
    last_short, last_long = last_two.iloc[1][s_col], last_two.iloc[1][l_col]
    if (prev_short <= prev_long) and (last_short > last_long):
        return 1
    if (prev_short >= prev_long) and (last_short < last_long):
        return -1
    return 0


def place_market_order(action: str, qty: int = QUANTITY):
    global paper_position, paper_capital, paper_entry_price
    
    # Check trading mode
    if TRADING_MODE == "paper" and PAPER_TRADING_ENABLED:
        # Paper Trading Mode - Simulate the order (NO API CALLS)
        logger.info(f"📝 PAPER TRADING: Simulating {action} MARKET order for {SYMBOL} qty={qty}")
        logger.info(f"   ✅ No API request used (paper trading)")
        
        try:
            current_price = last_ltp if last_ltp else 0
            if current_price == 0:
                logger.warning("No LTP available for paper trading simulation")
                return {"status": "error", "message": "No price available"}
            
            # Calculate trade value
            trade_value = current_price * qty
            
            # Simulate order execution
            if action == "BUY":
                if paper_position == 0:  # Opening long position
                    if paper_capital >= trade_value:
                        paper_position = qty
                        paper_entry_price = current_price
                        paper_capital -= trade_value
                        logger.info(f"✅ PAPER: Opened LONG position | Qty: {qty} | Price: ₹{current_price:.2f} | Capital: ₹{paper_capital:.2f}")
                    else:
                        logger.warning(f"❌ PAPER: Insufficient capital. Need: ₹{trade_value:.2f}, Available: ₹{paper_capital:.2f}")
                        return {"status": "error", "message": "Insufficient capital"}
                elif paper_position < 0:  # Closing short position
                    pnl = (paper_entry_price - current_price) * abs(paper_position)
                    paper_capital += (paper_entry_price * abs(paper_position)) + pnl
                    logger.info(f"✅ PAPER: Closed SHORT position | PnL: ₹{pnl:.2f} | Capital: ₹{paper_capital:.2f}")
                    paper_position = 0
                    paper_entry_price = 0
            
            elif action == "SELL":
                if paper_position == 0:  # Opening short position
                    paper_position = -qty
                    paper_entry_price = current_price
                    paper_capital += trade_value
                    logger.info(f"✅ PAPER: Opened SHORT position | Qty: {qty} | Price: ₹{current_price:.2f} | Capital: ₹{paper_capital:.2f}")
                elif paper_position > 0:  # Closing long position
                    pnl = (current_price - paper_entry_price) * paper_position
                    paper_capital += (current_price * paper_position)
                    logger.info(f"✅ PAPER: Closed LONG position | PnL: ₹{pnl:.2f} | Capital: ₹{paper_capital:.2f}")
                    paper_position = 0
                    paper_entry_price = 0
            
            # Log paper trade
            paper_trades.append({
                'time': datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': SYMBOL,
                'action': action,
                'quantity': qty,
                'price': current_price,
                'position': paper_position,
                'capital': paper_capital,
                'mode': 'PAPER'
            })
            
            trade_log.append({
                'time': datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': SYMBOL,
                'action': action,
                'quantity': qty,
                'price': current_price,
                'status': 'simulated',
                'orderid': f'PAPER_{len(paper_trades)}',
                'mode': 'PAPER'
            })
            
            return {"status": "success", "orderid": f"PAPER_{len(paper_trades)}", "mode": "paper"}
            
        except Exception as e:
            logger.exception("Paper trading simulation failed")
            return {"status": "error", "message": str(e)}
    
    else:
        # Live Trading Mode - Place real order with API limits
        # Check daily order limit
        if not check_order_limit():
            logger.error("Cannot place order - Daily order limit reached")
            return {"status": "error", "message": "Daily order limit reached"}
        
        # Check API request limit
        if not check_api_limit():
            logger.error("Cannot place order - API limit reached for today")
            return {"status": "error", "message": "API limit reached"}
        
        # Enforce Kite Connect's 3 requests/second limit
        enforce_rate_limit()
        
        logger.info(f"💰 LIVE TRADING: Placing {action} MARKET order for {SYMBOL} qty={qty}")
        logger.warning("⚠️  CAUTION: This is a REAL MONEY trade!")
        
        try:
            # Log API request and order
            log_api_request("placeorder")
            log_order(action)
            
            ltp = last_ltp if last_ltp else None
            resp = client.placeorder(
                strategy=STRATEGY_NAME,
                symbol=SYMBOL,
                exchange=EXCHANGE,
                action=action,
                price_type="MARKET",
                product=PRODUCT,
                quantity=qty
            )
            logger.info(f"Order response: {resp}")
            trade_log.append({
                'time': datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S'),
                'symbol': SYMBOL,
                'action': action,
                'quantity': qty,
                'price': ltp,
                'status': resp.get('status', 'unknown'),
                'orderid': resp.get('orderid', 'N/A'),
                'mode': 'LIVE'
            })
            return resp
        except Exception as e:
            logger.exception("Order placement failed")
            return {"status": "error", "message": str(e)}


# -----------------------------
# Auto Square-off at 15:20 IST
# -----------------------------

def auto_square_off():
    global paper_position, paper_capital, paper_entry_price
    
    try:
        now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")
        logger.info(f"{now} | Auto square-off triggered (closing all positions)")
        
        if TRADING_MODE == "paper" and PAPER_TRADING_ENABLED:
            # Paper trading square-off
            if paper_position != 0:
                current_price = last_ltp if last_ltp else 0
                if paper_position > 0:  # Close long
                    pnl = (current_price - paper_entry_price) * paper_position
                    paper_capital += (current_price * paper_position)
                    logger.info(f"📝 PAPER: Auto-squared LONG position | PnL: ₹{pnl:.2f} | Final Capital: ₹{paper_capital:.2f}")
                elif paper_position < 0:  # Close short
                    pnl = (paper_entry_price - current_price) * abs(paper_position)
                    paper_capital += (paper_entry_price * abs(paper_position)) + pnl
                    logger.info(f"📝 PAPER: Auto-squared SHORT position | PnL: ₹{pnl:.2f} | Final Capital: ₹{paper_capital:.2f}")
                
                paper_position = 0
                paper_entry_price = 0
            else:
                logger.info("📝 PAPER: No open positions to square off")
        else:
            # Live trading square-off
            if not check_api_limit():
                logger.error("Cannot square-off - API limit reached for today")
                return
            
            # Enforce rate limit
            enforce_rate_limit()
            
            # Log API request
            log_api_request("closeposition")
            
            response = client.closeposition(strategy=STRATEGY_NAME)
            logger.info(f"Square-off response: {response}")
            
    except Exception:
        logger.exception("Error during auto square-off")


# -----------------------------
# Daily Trade Report with PnL at 15:25 IST
# -----------------------------

def generate_daily_report():
    try:
        now = datetime.now(TIMEZONE).strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"{now} | Generating Daily Trade Report")
        
        # Save API usage log
        if api_request_log:
            api_log_file = f"api_usage_log_{datetime.now(TIMEZONE).strftime('%Y%m%d')}.csv"
            pd.DataFrame(api_request_log).to_csv(api_log_file, index=False)
            logger.info(f"API usage log saved to {api_log_file}")
        
        if not trade_log:
            logger.info("No trades executed today.")
            return
        
        df = pd.DataFrame(trade_log)

        # Calculate PnL assuming alternating BUY/SELL and using last_ltp as final exit price
        df['PnL'] = 0.0
        for i in range(1, len(df)):
            try:
                if df.loc[i - 1, 'action'] == 'BUY' and df.loc[i, 'action'] == 'SELL':
                    buy_price = pd.to_numeric(df.loc[i - 1, 'price'], errors='coerce') or 0.0
                    sell_price = pd.to_numeric(df.loc[i, 'price'], errors='coerce') or last_ltp or 0.0
                    quantity = pd.to_numeric(df.loc[i, 'quantity'], errors='coerce') or 1
                    df.loc[i, 'PnL'] = (sell_price - buy_price) * quantity
                elif df.loc[i - 1, 'action'] == 'SELL' and df.loc[i, 'action'] == 'BUY':
                    sell_price = pd.to_numeric(df.loc[i - 1, 'price'], errors='coerce') or 0.0
                    buy_price = pd.to_numeric(df.loc[i, 'price'], errors='coerce') or last_ltp or 0.0
                    quantity = pd.to_numeric(df.loc[i, 'quantity'], errors='coerce') or 1
                    df.loc[i, 'PnL'] = (sell_price - buy_price) * quantity
            except Exception as e:
                logger.warning(f"Error calculating PnL for trade {i}: {e}")
                df.loc[i, 'PnL'] = 0.0

        total_pnl = df['PnL'].sum()

        report_file = f"daily_trade_report_{datetime.now(TIMEZONE).strftime('%Y%m%d')}.csv"
        df.to_csv(report_file, index=False)

        logger.info("\n=== 📊 DAILY TRADE REPORT ===")
        logger.info(f"Trading Mode: {TRADING_MODE.upper()}")
        logger.info(f"API Requests Used: {api_request_count}/{MAX_API_REQUESTS_PER_DAY} ({int((api_request_count/MAX_API_REQUESTS_PER_DAY)*100)}%)")
        logger.info(f"Orders Placed: {order_count}/{MAX_ORDERS_PER_DAY}")
        logger.info(f"Rate Limit: {MAX_REQUESTS_PER_SECOND} requests/second (Kite Connect)")
        
        if TRADING_MODE == "paper" and PAPER_TRADING_ENABLED:
            logger.info(f"Starting Capital: ₹{PAPER_TRADING_CAPITAL:.2f}")
            logger.info(f"Current Capital: ₹{paper_capital:.2f}")
            logger.info(f"Total P&L: ₹{paper_capital - PAPER_TRADING_CAPITAL:.2f}")
            logger.info(f"Current Position: {paper_position} shares")
        
        logger.info(f"Total Trades: {len(df)} | Net PnL: ₹{total_pnl:.2f}")
        logger.info("\n" + df.to_string(index=False))
        logger.info(f"Report saved to {report_file}")
        logger.info("=============================")
    except Exception:
        logger.exception("Error generating daily report")


# -----------------------------
# Refresh Job
# -----------------------------

def refresh_and_evaluate():
    global bar_df, last_signal
    try:
        df = fetch_history(SYMBOL, EXCHANGE, INTERVAL, HISTORY_DAYS)
        
        # Check if we got valid data
        if df.empty:
            logger.warning("No historical data available, skipping evaluation")
            return
            
        df = compute_emas(df, SHORT_EMA, LONG_EMA)
        bar_df = df
        signal = detect_signal(df, SHORT_EMA, LONG_EMA)
        now = datetime.now(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S %Z")
        if signal == 1 and last_signal != 1:
            logger.info(f"{now} | Detected BULLISH crossover -> BUY")
            place_market_order("BUY")
            last_signal = 1
        elif signal == -1 and last_signal != -1:
            logger.info(f"{now} | Detected BEARISH crossover -> SELL")
            place_market_order("SELL")
            last_signal = -1
        else:
            logger.debug(f"{now} | No new crossover (signal={signal}, last_signal={last_signal})")
    except Exception:
        logger.exception("Error in refresh_and_evaluate")


# -----------------------------
# WebSocket / LTP subscription
# -----------------------------

def ltp_callback(data):
    global last_ltp
    try:
        logger.info(f"LTP Update: {data}")
        if isinstance(data, dict) and data.get("type") == "market_data":
            sym = data.get("symbol")
            exch = data.get("exchange")
            ltp = data.get("data", {}).get("ltp")
            ts = data.get("data", {}).get("timestamp")
            last_ltp = ltp
            logger.info(f"LTP {exch}:{sym}: {ltp} | Time: {ts}")
    except Exception:
        logger.exception("Error in ltp_callback")


# -----------------------------
# Main execution
# -----------------------------

def main():
    global last_signal
    refresh_and_evaluate()
    
    instruments = [{"exchange": EXCHANGE, "symbol": SYMBOL}]
    
    try:
        logger.info("Connecting to OpenAlgo WebSocket and subscribing to LTP updates...")
        client.connect()
        client.subscribe_ltp(instruments, on_data_received=ltp_callback)
    except Exception:
        logger.exception("WebSocket connection/subscribe failed")

    scheduler = BackgroundScheduler(timezone=TIMEZONE)
    scheduler.add_job(refresh_and_evaluate, 'interval', seconds=REFRESH_SECONDS, id='refresh_job')
    scheduler.add_job(auto_square_off, 'cron', hour=15, minute=20, id='auto_square_off')
    scheduler.add_job(generate_daily_report, 'cron', hour=15, minute=25, id='daily_report')
    scheduler.start()
    logger.info("Scheduler started. Running in Playground mode... Press Ctrl+C to exit.")

    try:
        while not stop_event.is_set():
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        scheduler.shutdown(wait=False)
        try:
            client.unsubscribe_ltp(instruments)
            client.disconnect()
        except Exception:
            pass


if __name__ == '__main__':
    print("🔁 OpenAlgo Python Bot is running.")
    print("=" * 60)
    if TRADING_MODE == "paper" and PAPER_TRADING_ENABLED:
        print("📝 PAPER TRADING MODE - NO REAL MONEY")
        print(f"💰 Starting Capital: ₹{PAPER_TRADING_CAPITAL:,.2f}")
        print("✅ Orders simulated - NO API quota used for trades")
    else:
        print("💰 LIVE TRADING MODE - REAL MONEY AT RISK!")
        print("⚠️  WARNING: Real trades will be executed!")
    print(f"📊 Rate Limit: {MAX_REQUESTS_PER_SECOND} req/sec (Kite Connect)")
    print(f"📊 Daily API Limit: {MAX_API_REQUESTS_PER_DAY} requests")
    print(f"📊 Daily Order Limit: {MAX_ORDERS_PER_DAY} orders")
    print("=" * 60)
    main()
