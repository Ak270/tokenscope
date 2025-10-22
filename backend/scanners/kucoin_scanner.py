"""
KuCoin Scanner - Detects new listings on KuCoin exchange
KuCoin has good volume and sometimes lists before Binance

API Docs: https://docs.kucoin.com/
"""

import aiohttp
from typing import List, Dict
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scanners.base_scanner import BaseScanner

class KuCoinScanner(BaseScanner):
    """Scanner for KuCoin exchange"""
    
    BASE_URL = 'https://api.kucoin.com'
    
    def __init__(self):
        super().__init__('KuCoin')
    
    async def fetch_all_pairs(self) -> List[str]:
        """
        Fetch all trading pairs from KuCoin
        Endpoint: GET /api/v1/symbols
        """
        
        url = f"{self.BASE_URL}/api/v1/symbols"
        
        try:
            async with self.session.get(url, timeout=10) as response:
                if response.status != 200:
                    raise Exception(f"KuCoin API error: {response.status}")
                
                data = await response.json()
                
                # KuCoin returns {code,  [...]}
                symbols_data = data.get('data', [])
                
                # Extract symbol names (format: BTC-USDT)
                pairs = [
                    item['symbol']
                    for item in symbols_data
                    if item.get('enableTrading', False)
                ]
                
                return pairs
                
        except Exception as e:
            print(f"[KuCoin] Error fetching pairs: {e}")
            return []
    
    async def get_pair_details(self, pair: str) -> Dict:
        """
        Get detailed info for a specific pair
        Endpoint: GET /api/v1/market/stats?symbol={pair}
        """
        
        url = f"{self.BASE_URL}/api/v1/market/stats"
        params = {'symbol': pair}
        
        try:
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status != 200:
                    return None
                
                result = await response.json()
                ticker = result.get('data', {})
                
                if not ticker:
                    return None
                
                # KuCoin format: BTC-USDT → extract BTC
                symbol = pair.split('-')[0] if '-' in pair else pair
                
                return {
                    'symbol': symbol,
                    'pair': pair,
                    'price': float(ticker.get('last', 0)),
                    'volume_24h': float(ticker.get('volValue', 0)),  # Volume in quote currency
                    'price_change_24h': float(ticker.get('changeRate', 0)) * 100,  # Convert to percentage
                    'high_24h': float(ticker.get('high', 0)),
                    'low_24h': float(ticker.get('low', 0)),
                    'listing_type': 'spot'
                }
                
        except Exception as e:
            print(f"[KuCoin] Error getting {pair} details: {e}")
            return None

# Test function
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("🔍 Testing KuCoin scanner...")
        
        async with KuCoinScanner() as scanner:
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
                print("✅ KuCoin scanner working correctly")
            
            # Show sample
            if scanner.last_scan_pairs:
                sample = list(scanner.last_scan_pairs)[:5]
                print(f"\nSample pairs: {sample}")
    
    asyncio.run(test())
