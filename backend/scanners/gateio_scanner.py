"""
Gate.io Scanner - Detects new listings on Gate.io
Gate.io often lists tokens 12-24h before Binance

API Docs: https://www.gate.io/docs/developers/apiv4/en/
"""

import aiohttp
from typing import List, Dict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from scanners.base_scanner import BaseScanner

class GateIOScanner(BaseScanner):
    """Scanner for Gate.io exchange"""
    
    BASE_URL = 'https://api.gateio.ws/api/v4'
    
    def __init__(self):
        super().__init__('Gate.io')
    
    async def fetch_all_pairs(self) -> List[str]:
        """
        Fetch all spot trading pairs from Gate.io
        Endpoint: GET /spot/currency_pairs
        """
        
        url = f"{self.BASE_URL}/spot/currency_pairs"
        
        async with self.session.get(url, timeout=10) as response:
            if response.status != 200:
                raise Exception(f"Gate.io API error: {response.status}")
            
            data = await response.json()
            
            # Extract pair IDs
            # Gate.io returns: [{"id": "BTC_USDT", "base": "BTC", "quote": "USDT", ...}, ...]
            pairs = [item['id'] for item in data if item.get('trade_status') == 'tradable']
            
            return pairs
    
    async def get_pair_details(self, pair: str) -> Dict:
        """
        Get detailed info for a specific pair
        Endpoint: GET /spot/tickers?currency_pair={pair}
        """
        
        url = f"{self.BASE_URL}/spot/tickers"
        params = {'currency_pair': pair}
        
        async with self.session.get(url, params=params, timeout=10) as response:
            if response.status != 200:
                return None
            
            data = await response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            ticker = data[0]  # Returns array with 1 item
            
            # Parse symbol (BTC_USDT → BTC)
            base = pair.split('_')[0]
            
            return {
                'symbol': base,
                'pair': pair,
                'price': float(ticker.get('last', 0)),
                'volume_24h': float(ticker.get('quote_volume', 0)),  # Volume in USDT
                'price_change_24h': float(ticker.get('change_percentage', 0)),
                'high_24h': float(ticker.get('high_24h', 0)),
                'low_24h': float(ticker.get('low_24h', 0)),
                'listing_type': 'spot'
            }

# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        async with GateIOScanner() as scanner:
            print("🔍 Testing Gate.io scanner...")
            
            # First scan (establishes baseline)
            print("\n1st scan (baseline)...")
            result1 = await scanner.scan()
            print(f"Found {len(result1)} pairs initially")
            
            # Second scan (should find no new listings)
            print("\n2nd scan (should find nothing new)...")
            result2 = await scanner.scan()
            print(f"Found {len(result2)} new listings")
            
            if len(result2) == 0:
                print("✅ Scanner working correctly - no false positives")
            
            # Show sample data
            if scanner.last_scan_pairs:
                sample_pairs = list(scanner.last_scan_pairs)[:5]
                print(f"\nSample pairs tracked: {sample_pairs}")
    
    asyncio.run(test())
