"""
Telegram Alert System
Sends instant notifications when opportunities are detected
"""

import asyncio
from telegram import Bot
from telegram.error import TelegramError
from typing import Dict
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

class TelegramNotifier:
    """Send alerts via Telegram"""
    
    def __init__(self):
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self.chat_id = config.TELEGRAM_CHAT_ID
        
        if not self.bot_token or not self.chat_id:
            print("⚠️ Telegram not configured - alerts disabled")
            self.enabled = False
        else:
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
    
    async def send_new_listing_alert(self, listing: Dict) -> bool:
        """
        Send alert for new listing detected
        """
        
        if not self.enabled:
            print("Telegram disabled - would have sent alert")
            return False
        
        message = self._format_new_listing_message(listing)
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
            print(f"✅ Telegram alert sent for {listing['symbol']}")
            return True
            
        except TelegramError as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def _format_new_listing_message(self, listing: Dict) -> str:
        """
        Format listing data into readable Telegram message
        """
        
        symbol = listing['symbol']
        exchange = listing['exchange']
        price = listing.get('price', 'N/A')
        volume = listing.get('volume_24h', 0)
        change = listing.get('price_change_24h', 0)
        
        # Format volume
        if volume > 1000000:
            volume_str = f"${volume/1000000:.2f}M"
        elif volume > 1000:
            volume_str = f"${volume/1000:.1f}K"
        else:
            volume_str = f"${volume:.0f}"
        
        # Determine urgency emoji
        if exchange == 'Gate.io':
            urgency = "🔥🔥🔥"  # High priority - usually early
        elif exchange == 'MEXC':
            urgency = "🔥🔥"    # Medium priority
        else:
            urgency = "🔥"      # Normal priority
        
        message = f"""
{urgency} <b>NEW LISTING DETECTED</b> {urgency}

<b>Token:</b> {symbol}
<b>Exchange:</b> {exchange}
<b>Price:</b> ${price}
<b>24h Volume:</b> {volume_str}
<b>24h Change:</b> {change:+.2f}%

<b>⚡️ QUICK ACTION:</b>
• Check Binance for announcement
• Monitor for Binance listing (12-24h window)
• Consider entry if volume > $1M

<i>Detected at: {listing.get('detected_at', 'N/A')}</i>
        """.strip()
        
        return message
    
    async def send_opportunity_alert(self, opportunity: Dict) -> bool:
        """
        Send alert for high-probability opportunity
        (When we detect Gate.io listing + Binance might list soon)
        """
        
        if not self.enabled:
            return False
        
        message = self._format_opportunity_message(opportunity)
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML'
            )
            return True
        except TelegramError as e:
            print(f"❌ Telegram error: {e}")
            return False
    
    def _format_opportunity_message(self, opp: Dict) -> str:
        """
        Format trading opportunity alert
        """
        
        symbol = opp['symbol']
        action = opp['action']  # BUY/SELL/WAIT
        entry_price = opp.get('entry_price', 0)
        target_1 = opp.get('target_1', 0)
        target_2 = opp.get('target_2', 0)
        stop_loss = opp.get('stop_loss', 0)
        confidence = opp.get('confidence', 0)
        
        # Calculate potential profit
        if entry_price and target_1:
            profit_pct = ((target_1 - entry_price) / entry_price) * 100
        else:
            profit_pct = 0
        
        message = f"""
🎯 <b>TRADING OPPORTUNITY</b> 🎯

<b>Token:</b> {symbol}
<b>Action:</b> {action}
<b>Confidence:</b> {confidence}%

<b>📈 ENTRY:</b>
Buy at: ${entry_price:.6f}
Buy on: {opp.get('buy_exchange', 'Gate.io')}

<b>🎯 TARGETS:</b>
Target 1: ${target_1:.6f} (+{profit_pct:.1f}%)
Target 2: ${target_2:.6f} (+{((target_2 - entry_price) / entry_price) * 100:.1f}%)

<b>🛑 RISK MANAGEMENT:</b>
Stop Loss: ${stop_loss:.6f} ({((stop_loss - entry_price) / entry_price) * 100:.1f}%)
Position Size: {opp.get('position_size', '2-3%')} of portfolio

<b>⏰ TIME WINDOW:</b>
{opp.get('time_window', 'Execute within 24 hours')}

<b>💡 REASONING:</b>
{opp.get('reasoning', 'AI-generated signal')}
        """.strip()
        
        return message

# Test function
if __name__ == "__main__":
    async def test():
        notifier = TelegramNotifier()
        
        # Test listing alert
        test_listing = {
            'symbol': 'TEST',
            'exchange': 'Gate.io',
            'price': 0.025,
            'volume_24h': 1500000,
            'price_change_24h': 45.5,
            'detected_at': '2025-10-22T14:30:00Z'
        }
        
        print("📤 Sending test alert...")
        await notifier.send_new_listing_alert(test_listing)
        print("✅ Check your Telegram!")
    
    asyncio.run(test())
