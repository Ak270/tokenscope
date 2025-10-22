"""
MEXC Scanner - Detects new listings on MEXC exchange
MEXC lists tokens 6-24h before Binance (similar to Gate.io)

API Docs: https://mexcdevelop.github.io/apidocs/spot_v3_en/
"""

import aiohttp
from typing import List, Dict
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scanners.base_scanner import BaseScanner

class MEXCScanner(BaseScanner):
    """Scanner for MEXC exchange"""
    
    BASE_URL = 'https://api.mexc.com'
    
    def __init__(self):
        super().__init__('MEXC')
    
    async def fetch_all_pairs(self) -> List[str]:
        """
        Fetch all spot trading pairs from MEXC
        Endpoint: GET /api/v3/exchangeInfo
        """
        
        url = f"{self.BASE_URL}/api/v3/exchangeInfo"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"MEXC API error: {response.status}")
                
                data = await response.json()
                
                # Extract symbols that are trading
                pairs = [
                    item['symbol'] 
                    for item in data.get('symbols', [])
                    if item.get('status') == 'ENABLED'
                ]
                
                return pairs
                
        except Exception as e:
            print(f"[MEXC] Error fetching pairs: {e}")
            return []
    
    async def get_pair_details(self, pair: str) -> Dict:
        """
        Get detailed info for a specific pair
        Endpoint: GET /api/v3/ticker/24hr?symbol={pair}
        """
        
        url = f"{self.BASE_URL}/api/v3/ticker/24hr"
        params = {'symbol': pair}
        
        try:
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    return None
                
                ticker = await response.json()
                
                # MEXC format: BTCUSDT → extract BTC
                # Remove common quote currencies
                quote_currencies = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB']
                symbol = pair
                for quote in quote_currencies:
                    if pair.endswith(quote):
                        symbol = pair[:-len(quote)]
                        break
                
                return {
                    'symbol': symbol,
                    'pair': pair,
                    'price': float(ticker.get('lastPrice', 0)),
                    'volume_24h': float(ticker.get('quoteVolume', 0)),  # Volume in USDT
                    'price_change_24h': float(ticker.get('priceChangePercent', 0)),
                    'high_24h': float(ticker.get('highPrice', 0)),
                    'low_24h': float(ticker.get('lowPrice', 0)),
                    'listing_type': 'spot'
                }
                
        except Exception as e:
            print(f"[MEXC] Error getting {pair} details: {e}")
            return None

# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("🔍 Testing MEXC scanner...")
        
        async with MEXCScanner() as scanner:
            # First scan
            print("\n1st scan (baseline)...")
            result1 = await scanner.scan()
            print(f"Found {len(result1)} pairs initially")
            print(f"Tracking {len(scanner.last_scan_pairs)} total pairs")
            
            # Second scan
            print("\n2nd scan...")
            result2 = await scanner.scan()
            print(f"Found {len(result2)} new listings")
            
            if len(result2) == 0:
                print("✅ MEXC scanner working correctly")
            
            # Show sample
            if scanner.last_scan_pairs:
                sample = list(scanner.last_scan_pairs)[:5]
                print(f"\nSample pairs: {sample}")
    
    asyncio.run(test())
