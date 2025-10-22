"""
Price Aggregator - Finds best prices across all exchanges
Critical for identifying arbitrage opportunities
"""

import aiohttp
import asyncio
from typing import Dict, List, Optional
from datetime import datetime

class PriceAggregator:
    """Aggregate prices from multiple exchanges"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_all_prices(self, symbol: str) -> Dict:
        """
        Get price for a symbol from all exchanges
        
        Returns:
        {
            'symbol': 'BTC',
            'prices': {
                'Gate.io': {'price': 43500, 'volume_24h': 1250000},
                'MEXC': {'price': 43520, 'volume_24h': 980000},
                'KuCoin': {'price': 43490, 'volume_24h': 1100000},
                'Binance': {'price': 43550, 'volume_24h': 5500000}
            },
            'best_buy': {'exchange': 'KuCoin', 'price': 43490},
            'best_sell': {'exchange': 'Binance', 'price': 43550},
            'arbitrage_opportunity': {
                'buy_on': 'KuCoin',
                'sell_on': 'Binance',
                'profit_pct': 0.14
            }
        }
        """
        
        # Fetch from all exchanges in parallel
        tasks = [
            self._get_gateio_price(symbol),
            self._get_mexc_price(symbol),
            self._get_kucoin_price(symbol),
            self._get_binance_price(symbol)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        prices = {}
        for result in results:
            if isinstance(result, dict) and 'exchange' in result:
                prices[result['exchange']] = {
                    'price': result['price'],
                    'volume_24h': result['volume_24h']
                }
        
        if not prices:
            return {'symbol': symbol, 'error': 'No prices found'}
        
        # Find best prices
        best_buy = min(prices.items(), key=lambda x: x[1]['price'])
        best_sell = max(prices.items(), key=lambda x: x[1]['price'])
        
        # Calculate arbitrage opportunity
        arb_profit_pct = ((best_sell[1]['price'] - best_buy[1]['price']) / best_buy[1]['price']) * 100
        
        return {
            'symbol': symbol,
            'prices': prices,
            'best_buy': {
                'exchange': best_buy[0],
                'price': best_buy[1]['price']
            },
            'best_sell': {
                'exchange': best_sell[0],
                'price': best_sell[1]['price']
            },
            'arbitrage_opportunity': {
                'buy_on': best_buy[0],
                'sell_on': best_sell[0],
                'profit_pct': round(arb_profit_pct, 2),
                'profitable': arb_profit_pct > 1.0  # Minimum 1% profit to be worth it
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
    
    async def _get_gateio_price(self, symbol: str) -> Optional[Dict]:
        """Get price from Gate.io"""
        try:
            # Try common pairs
            pairs_to_try = [f"{symbol}_USDT", f"{symbol}_USD"]
            
            for pair in pairs_to_try:
                url = f"https://api.gateio.ws/api/v4/spot/tickers"
                params = {'currency_pair': pair}
                
                async with self.session.get(url, params=params, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        if not data or not isinstance(data, list):
                            return {
                                'exchange': 'Gate.io',
                                'price': float(data[0].get('last', 0)),
                                'volume_24h': float(data[0].get('quote_volume', 0))
                            }
            return None
        except:
            return None
    
    async def _get_mexc_price(self, symbol: str) -> Optional[Dict]:
        """Get price from MEXC"""
        try:
            pair = f"{symbol}USDT"
            url = f"https://api.mexc.com/api/v3/ticker/24hr"
            params = {'symbol': pair}
            
            async with self.session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'exchange': 'MEXC',
                        'price': float(data.get('lastPrice', 0)),
                        'volume_24h': float(data.get('quoteVolume', 0))
                    }
            return None
        except:
            return None
    
    async def _get_kucoin_price(self, symbol: str) -> Optional[Dict]:
        """Get price from KuCoin"""
        try:
            pair = f"{symbol}-USDT"
            url = f"https://api.kucoin.com/api/v1/market/stats"
            params = {'symbol': pair}
            
            async with self.session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    result = await response.json()
                    data = result.get('data', {})
                    if not data or not isinstance(data, list):
                        return {
                            'exchange': 'KuCoin',
                            'price': float(data.get('last', 0)),
                            'volume_24h': float(data.get('volValue', 0))
                        }
            return None
        except:
            return None
    
    async def _get_binance_price(self, symbol: str) -> Optional[Dict]:
        """Get price from Binance"""
        try:
            pair = f"{symbol}USDT"
            url = f"https://api.binance.com/api/v3/ticker/24hr"
            params = {'symbol': pair}
            
            async with self.session.get(url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'exchange': 'Binance',
                        'price': float(data.get('lastPrice', 0)),
                        'volume_24h': float(data.get('quoteVolume', 0))
                    }
            return None
        except:
            return None

# Test
if __name__ == "__main__":
    async def test():
        print("💰 Testing Price Aggregator...")
        
        async with PriceAggregator() as aggregator:
            # Test with BTC (available on all exchanges)
            print("\n📊 Testing with BTC...")
            result = await aggregator.get_all_prices('BTC')
            
            if 'error' in result:
                print(f"Error: {result['error']}")
            else:
                print(f"\nSymbol: {result['symbol']}")
                print("\nPrices across exchanges:")
                for exchange, data in result['prices'].items():
                    print(f"  {exchange}: ${data['price']:,.2f} (Vol: ${data['volume_24h']:,.0f})")
                
                print(f"\n💵 Best place to BUY: {result['best_buy']['exchange']} at ${result['best_buy']['price']:,.2f}")
                print(f"💰 Best place to SELL: {result['best_sell']['exchange']} at ${result['best_sell']['price']:,.2f}")
                
                arb = result['arbitrage_opportunity']
                if arb['profitable']:
                    print(f"\n🎯 ARBITRAGE OPPORTUNITY:")
                    print(f"   Buy on {arb['buy_on']}, sell on {arb['sell_on']}")
                    print(f"   Potential profit: {arb['profit_pct']}%")
                else:
                    print(f"\n   No significant arbitrage opportunity ({arb['profit_pct']}%)")
    
    asyncio.run(test())
