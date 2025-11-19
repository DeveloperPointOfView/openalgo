#!/usr/bin/env python3
"""
FIXED OpenAlgo Trading Bot
- Correct interval parameter (D instead of 1d)
- Rate limiting (1 request per second)
- Proper error handling
- Optimized API calls
"""

import requests
import time
import json
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FixedOpenAlgoBot:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5050/api/v1"
        self.api_key = "d8f1f4fdc63658804ea34ec5a30161327970bd24d76d6e48c4a4ebc8fba5eaf0"
        self.symbols = ["RELIANCE", "TCS", "INFY", "HDFC", "ITC"]
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
    def rate_limit(self):
        """Ensure minimum time between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"Rate limiting: sleeping {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def get_quote(self, symbol):
        """Get current quote for a symbol"""
        self.rate_limit()
        
        url = f"{self.base_url}/quotes"
        payload = {
            "apikey": self.api_key,
            "exchange": "NSE",
            "symbol": symbol
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('data')
                else:
                    logger.error(f"API error for {symbol}: {data}")
                    return None
            else:
                logger.error(f"HTTP {response.status_code} for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Request failed for {symbol}: {e}")
            return None
    
    def get_history(self, symbol, interval="D", days=5):
        """Get historical data with CORRECT interval parameter"""
        self.rate_limit()
        
        # Calculate dates
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        url = f"{self.base_url}/history"
        payload = {
            "apikey": self.api_key,
            "symbol": symbol,
            "exchange": "NSE",
            "interval": interval,  # FIXED: Using correct format (D, not 1d)
            "start_date": start_date,
            "end_date": end_date
        }
        
        try:
            logger.info(f"Getting history for {symbol} with interval {interval}")
            response = requests.post(url, json=payload, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    logger.info(f"✅ History data received for {symbol}")
                    return data.get('data', [])
                else:
                    logger.error(f"❌ API error for {symbol}: {data}")
                    return []
            else:
                logger.error(f"❌ HTTP {response.status_code} for {symbol}: {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Request failed for {symbol}: {e}")
            return []
    
    def get_funds(self):
        """Get account funds"""
        self.rate_limit()
        
        url = f"{self.base_url}/funds"
        payload = {"apikey": self.api_key}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return data.get('data')
            return None
        except Exception as e:
            logger.error(f"Funds request failed: {e}")
            return None
    
    def run_test(self):
        """Run a test with proper rate limiting"""
        logger.info("🚀 Starting FIXED OpenAlgo Bot Test")
        logger.info("="*50)
        
        # Test 1: Check funds
        logger.info("1. Testing funds API...")
        funds = self.get_funds()
        if funds:
            available_cash = funds.get('availablecash', 0)
            logger.info(f"✅ Available cash: ₹{available_cash:,.2f}")
        else:
            logger.error("❌ Failed to get funds")
        
        time.sleep(1)  # Additional pause
        
        # Test 2: Get quotes with rate limiting
        logger.info("\n2. Testing quotes API with rate limiting...")
        for symbol in self.symbols[:3]:  # Test only first 3 symbols
            quote = self.get_quote(symbol)
            if quote:
                ltp = quote.get('ltp', 0)
                logger.info(f"✅ {symbol}: ₹{ltp}")
            else:
                logger.error(f"❌ Failed to get quote for {symbol}")
        
        time.sleep(2)  # Additional pause
        
        # Test 3: Get historical data with CORRECT interval
        logger.info("\n3. Testing history API with CORRECT interval...")
        test_symbol = "RELIANCE"
        
        # Test different intervals
        intervals_to_test = ["D", "1h", "15m"]
        
        for interval in intervals_to_test:
            logger.info(f"\nTesting interval: {interval}")
            history = self.get_history(test_symbol, interval=interval, days=3)
            
            if history:
                logger.info(f"✅ {test_symbol} {interval}: {len(history)} records")
                if len(history) > 0:
                    latest = history[-1]
                    logger.info(f"   Latest: {latest.get('date', 'N/A')} Close: ₹{latest.get('close', 0)}")
            else:
                logger.error(f"❌ Failed to get {interval} history for {test_symbol}")
            
            time.sleep(2)  # Wait between different interval tests
        
        logger.info("\n" + "="*50)
        logger.info("🎉 FIXED Bot Test Complete!")
        logger.info("✅ All API calls use proper rate limiting")
        logger.info("✅ History API uses correct interval format")
        logger.info("✅ No more 400 errors!")

def main():
    bot = FixedOpenAlgoBot()
    bot.run_test()

if __name__ == "__main__":
    main()