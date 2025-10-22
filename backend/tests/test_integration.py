"""
Integration test: Gate.io scanner → Telegram alert
"""

import asyncio
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scanners.gateio_scanner import GateIOScanner
from services.telegram_notifier import TelegramNotifier

async def test_full_flow():
    """Test the complete detection → alert flow"""
    
    print("🧪 INTEGRATION TEST: Gate.io → Telegram")
    print("="*60)
    
    # Initialize components
    notifier = TelegramNotifier()
    
    async with GateIOScanner() as scanner:
        
        # Step 1: First scan (baseline)
        print("\n1️⃣ Running baseline scan...")
        baseline = await scanner.scan()
        print(f"   Tracked {len(scanner.last_scan_pairs)} pairs")
        
        # Step 2: Simulate new listing
        print("\n2️⃣ Simulating new listing detection...")
        
        # Get a real pair for realistic data
        if scanner.last_scan_pairs:
            sample_pair = list(scanner.last_scan_pairs)[0]
            details = await scanner.get_pair_details(sample_pair)
            
            if details:
                # Modify to look like new listing
                details['symbol'] = 'NEWSIM'  # Fake symbol
                details['exchange'] = 'Gate.io'
                
                print(f"   Simulated listing: {details['symbol']}")
                
                # Step 3: Send alert
                print("\n3️⃣ Sending Telegram alert...")
                success = await notifier.send_new_listing_alert(details)
                
                if success:
                    print("\n✅ INTEGRATION TEST PASSED!")
                    print("   Check your Telegram for alert")
                else:
                    print("\n❌ Alert failed to send")
            else:
                print("   Could not get pair details")
        else:
            print("   No pairs to test with")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    asyncio.run(test_full_flow())
