"""
Alert Manager
Decides when and what to send via Telegram
"""

import asyncio
from typing import List
from datetime import datetime
from pymongo import MongoClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

from services.telegram_notifier import TelegramNotifier

class AlertManager:
    """Manage alert sending logic"""
    
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client['tokenscope']
        self.opportunities_collection = self.db['opportunities']
        self.listings_collection = self.db['listings']
        self.notifier = TelegramNotifier()
    
    async def send_pending_alerts(self) -> int:
        """
        Send alerts for opportunities that haven't been alerted yet
        Returns: Number of alerts sent
        """
        
        # Find opportunities that need alerts
        pending = list(self.opportunities_collection.find({
            'alert_sent': {'$ne': True}
        }).sort('urgency', -1))  # CRITICAL first, then HIGH, then NORMAL
        
        if not pending:
            print("📭 No pending alerts")
            return 0
        
        print(f"\n📤 Found {len(pending)} pending alerts")
        
        alerts_sent = 0
        
        for opportunity in pending:
            try:
                success = await self._send_opportunity_alert(opportunity)
                
                if success:
                    # Mark as sent
                    self.opportunities_collection.update_one(
                        {'_id': opportunity['_id']},
                        {'$set': {
                            'alert_sent': True,
                            'alert_sent_at': datetime.utcnow().isoformat() + 'Z'
                        }}
                    )
                    
                    # Also mark the original listing
                    self.listings_collection.update_one(
                        {
                            'symbol': opportunity['symbol'],
                            'exchange': opportunity['source_exchange']
                        },
                        {'$set': {'alert_sent': True}}
                    )
                    
                    alerts_sent += 1
                    print(f"   ✅ Alert sent for {opportunity['symbol']}")
                    
                    # Rate limit: Don't spam Telegram
                    await asyncio.sleep(2)
                
            except Exception as e:
                print(f"   ❌ Error sending alert for {opportunity.get('symbol')}: {e}")
        
        return alerts_sent
    
    async def _send_opportunity_alert(self, opportunity: Dict) -> bool:
        """Send alert for a specific opportunity"""
        
        urgency = opportunity.get('urgency', 'NORMAL')
        
        # Format opportunity for Telegram
        alert_data = {
            'symbol': opportunity['symbol'],
            'action': self._determine_action(opportunity),
            'urgency': urgency,
            'entry_price': opportunity['strategy']['entry_price'],
            'buy_exchange': opportunity['strategy']['entry_exchange'],
            'target_1': opportunity['strategy']['target_1'],
            'target_2': opportunity['strategy']['target_2'],
            'stop_loss': opportunity['strategy']['stop_loss'],
            'position_size': opportunity['strategy']['position_size'],
            'time_window': opportunity['strategy']['time_window'],
            'confidence': opportunity.get('ai_recommendation', {}).get('confidence', 50),
            'reasoning': opportunity.get('reason', 'New listing detected')
        }
        
        # Add AI analysis if available
        if 'ai_recommendation' in opportunity:
            ai = opportunity['ai_recommendation']
            if 'ai_analysis' in ai:
                alert_data['reasoning'] = ai['ai_analysis'][:200] + '...'  # Truncate
        
        # Send appropriate alert type
        if urgency in ['HIGH', 'CRITICAL']:
            return await self.notifier.send_opportunity_alert(alert_data)
        else:
            # For NORMAL urgency, just send simple new listing alert
            listing_data = {
                'symbol': opportunity['symbol'],
                'exchange': opportunity['source_exchange'],
                'price': opportunity['strategy']['entry_price'],
                'detected_at': opportunity['detected_at']
            }
            return await self.notifier.send_new_listing_alert(listing_data)
    
    def _determine_action(self, opportunity: Dict) -> str:
        """Determine action recommendation"""
        
        urgency = opportunity.get('urgency', 'NORMAL')
        opp_type = opportunity.get('opportunity_type', '')
        
        if urgency == 'CRITICAL':
            return 'BUY NOW'
        elif urgency == 'HIGH' and opp_type == 'PRE_BINANCE_LISTING':
            return 'BUY (Pre-Binance)'
        elif opp_type == 'ARBITRAGE':
            return 'ARBITRAGE'
        else:
            return 'WATCH'

# CLI entry point
if __name__ == "__main__":
    async def main():
        print("📤 TokenScope Alert Manager")
        print("="*60)
        
        manager = AlertManager()
        count = await manager.send_pending_alerts()
        
        print("\n" + "="*60)
        print(f"✅ Sent {count} alerts")
    
    asyncio.run(main())
