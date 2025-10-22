"""
Opportunity Detector
Analyzes new listings and determines if they're worth alerting
"""

import asyncio
from typing import Dict, Optional
from datetime import datetime
from pymongo import MongoClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

from services.price_aggregator import PriceAggregator
from services.ai_analyzer import analyze_token_with_ai

class OpportunityDetector:
    """Detect trading opportunities in new listings"""
    
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client['tokenscope']
        self.listings_collection = self.db['listings']
        self.opportunities_collection = self.db['opportunities']
    
    async def analyze_listing(self, listing: Dict) -> Optional[Dict]:
        """
        Analyze a listing to determine if it's an opportunity
        
        Returns opportunity dict if worth alerting, None otherwise
        """
        
        symbol = listing['symbol']
        exchange = listing['exchange']
        
        print(f"\n🔍 Analyzing {symbol} from {exchange}...")
        
        # Step 1: Get prices from all exchanges
        async with PriceAggregator() as aggregator:
            price_data = await aggregator.get_all_prices(symbol)
        
        if 'error' in price_
            print(f"   ⚠️ Could not get price data")
            return None
        
        # Step 2: Check if there's arbitrage opportunity
        arb = price_data.get('arbitrage_opportunity', {})
        
        # Step 3: Determine opportunity type and urgency
        opportunity = {
            'symbol': symbol,
            'detected_at': listing.get('detected_at'),
            'source_exchange': exchange,
            'opportunity_type': self._classify_opportunity(listing, price_data),
            'price_data': price_data,
            'urgency': 'NORMAL'
        }
        
        # HIGH URGENCY: Listed on Gate.io/MEXC but NOT on Binance
        if exchange in ['Gate.io', 'MEXC']:
            if 'Binance' not in price_data.get('prices', {}):
                opportunity['urgency'] = 'HIGH'
                opportunity['reason'] = f"Listed on {exchange} but NOT on Binance yet - potential pre-listing opportunity"
                print(f"   🔥 HIGH URGENCY: Not on Binance yet!")
        
        # CRITICAL: Large arbitrage opportunity (>2%)
        if arb.get('profit_pct', 0) > 2.0:
            opportunity['urgency'] = 'CRITICAL'
            opportunity['arbitrage'] = arb
            print(f"   💰 ARBITRAGE: {arb['profit_pct']}% profit potential!")
        
        # Step 4: Generate AI recommendation (if high/critical urgency)
        if opportunity['urgency'] in ['HIGH', 'CRITICAL']:
            opportunity['ai_recommendation'] = await self._get_ai_recommendation(
                symbol, 
                listing,
                price_data
            )
        
        # Step 5: Calculate entry/exit strategy
        opportunity['strategy'] = self._calculate_strategy(listing, price_data, opportunity['urgency'])
        
        return opportunity
    
    def _classify_opportunity(self, listing: Dict, price_ Dict) -> str:
        """Classify the type of opportunity"""
        
        exchange = listing['exchange']
        prices = price_data.get('prices', {})
        
        if exchange in ['Gate.io', 'MEXC'] and 'Binance' not in prices:
            return 'PRE_BINANCE_LISTING'
        elif len(prices) > 1:
            return 'ARBITRAGE'
        elif exchange == 'Binance':
            return 'BINANCE_LISTING'
        else:
            return 'NEW_LISTING'
    
    def _calculate_strategy(self, listing: Dict, price_ Dict, urgency: str) -> Dict:
        """Calculate entry/exit strategy"""
        
        best_buy = price_data.get('best_buy', {})
        best_sell = price_data.get('best_sell', {})
        
        entry_price = best_buy.get('price', 0)
        
        if entry_price == 0:
            return {'error': 'No valid entry price'}
        
        # Conservative targets based on urgency
        if urgency == 'CRITICAL':
            # High confidence - aggressive targets
            targets = {
                'target_1': entry_price * 1.50,  # 50% profit
                'target_2': entry_price * 2.00,  # 100% profit
                'stop_loss': entry_price * 0.85  # 15% stop loss
            }
        elif urgency == 'HIGH':
            # Medium confidence - moderate targets
            targets = {
                'target_1': entry_price * 1.30,  # 30% profit
                'target_2': entry_price * 1.60,  # 60% profit
                'stop_loss': entry_price * 0.90  # 10% stop loss
            }
        else:
            # Low confidence - conservative targets
            targets = {
                'target_1': entry_price * 1.20,  # 20% profit
                'target_2': entry_price * 1.40,  # 40% profit
                'stop_loss': entry_price * 0.92  # 8% stop loss
            }
        
        return {
            'entry_exchange': best_buy.get('exchange'),
            'entry_price': entry_price,
            'target_1': round(targets['target_1'], 6),
            'target_2': round(targets['target_2'], 6),
            'stop_loss': round(targets['stop_loss'], 6),
            'position_size': '2-3%' if urgency == 'HIGH' else '1-2%',
            'time_window': '12-24 hours' if urgency == 'HIGH' else '24-48 hours'
        }
    
    async def _get_ai_recommendation(self, symbol: str, listing: Dict, price_ Dict) -> Dict:
        """Get AI analysis for the opportunity"""
        
        # Prepare token data for AI
        token_data = {
            'name': listing.get('name', symbol),
            'symbol': symbol,
            'exchange': listing.get('exchange'),
            'chain': listing.get('chain', 'Unknown'),
            'price_data': {
                'current_price_usd': price_data['best_buy']['price'],
                'price_change_24h': 0,  # New listing
                'volume_24h': sum(p.get('volume_24h', 0) for p in price_data['prices'].values())
            }
        }
        
        try:
            ai_result = analyze_token_with_ai(token_data)
            return ai_result
        except Exception as e:
            print(f"   ⚠️ AI analysis failed: {e}")
            return {'action': 'MANUAL_REVIEW', 'confidence': 0}
    
    async def process_new_listings(self) -> int:
        """
        Process all new listings that haven't been analyzed yet
        Returns: Number of opportunities detected
        """
        
        # Find listings that haven't been analyzed
        new_listings = list(self.listings_collection.find({
            'data_enriched': False,
            'alert_sent': False
        }))
        
        if not new_listings:
            print("📭 No new listings to analyze")
            return 0
        
        print(f"\n📊 Found {len(new_listings)} new listings to analyze")
        
        opportunities_found = 0
        
        for listing in new_listings:
            try:
                opportunity = await self.analyze_listing(listing)
                
                if opportunity:
                    # Save opportunity
                    opportunity['created_at'] = datetime.utcnow().isoformat() + 'Z'
                    self.opportunities_collection.insert_one(opportunity)
                    opportunities_found += 1
                    
                    print(f"   ✅ Opportunity detected: {opportunity['urgency']}")
                
                # Mark as enriched
                self.listings_collection.update_one(
                    {'_id': listing['_id']},
                    {'$set': {'data_enriched': True}}
                )
                
            except Exception as e:
                print(f"   ❌ Error analyzing {listing.get('symbol')}: {e}")
        
        return opportunities_found

# CLI entry point
if __name__ == "__main__":
    async def main():
        print("🔍 TokenScope Opportunity Detector")
        print("="*60)
        
        detector = OpportunityDetector()
        count = await detector.process_new_listings()
        
        print("\n" + "="*60)
        print(f"✅ Detected {count} opportunities")
    
    asyncio.run(main())
