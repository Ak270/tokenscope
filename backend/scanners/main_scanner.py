"""
Main Scanner Orchestrator
Runs all exchange scanners in parallel and coordinates results
"""

import asyncio
from typing import List, Dict
from datetime import datetime
from pymongo import MongoClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import config

from scanners.gateio_scanner import GateIOScanner
from scanners.mexc_scanner import MEXCScanner
from scanners.kucoin_scanner import KuCoinScanner
from scanners.binance_scanner import BinanceScanner

class MainScanner:
    """Orchestrates all exchange scanners"""
    
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URI)
        self.db = self.client['tokenscope']
        self.listings_collection = self.db['listings']
    
    async def run_all_scanners(self) -> List[Dict]:
        """
        Run all scanners in parallel
        Returns: List of all newly detected listings
        """
        
        print("🔍 Running all exchange scanners...")
        print("="*60)
        
        # Initialize all scanners
        scanners = []
        
        try:
            # Run all scanners concurrently
            async with GateIOScanner() as gateio, \
                       MEXCScanner() as mexc, \
                       KuCoinScanner() as kucoin, \
                       BinanceScanner() as binance:
                
                tasks = [
                    gateio.scan(),
                    mexc.scan(),
                    kucoin.scan(),
                    binance.scan()
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Combine all results
                all_new_listings = []
                
                for i, result in enumerate(results):
                    scanner_name = ['Gate.io', 'MEXC', 'KuCoin', 'Binance'][i]
                    
                    if isinstance(result, Exception):
                        print(f"❌ {scanner_name} failed: {result}")
                    elif isinstance(result, list):
                        print(f"✅ {scanner_name}: Found {len(result)} new listing(s)")
                        all_new_listings.extend(result)
                    else:
                        print(f"⚠️ {scanner_name}: Unexpected result type")
                
                return all_new_listings
                
        except Exception as e:
            print(f"❌ Scanner orchestrator error: {e}")
            return []
    
    def save_listings_to_db(self, listings: List[Dict]) -> int:
        """
        Save new listings to MongoDB
        Returns: Number of listings saved
        """
        
        if not listings:
            return 0
        
        saved_count = 0
        
        for listing in listings:
            try:
                # Check if already exists
                existing = self.listings_collection.find_one({
                    'symbol': listing['symbol'],
                    'exchange': listing['exchange']
                })
                
                if existing:
                    print(f"   ⚠️ {listing['symbol']} on {listing['exchange']} already in DB")
                    continue
                
                # Add metadata
                listing['saved_at'] = datetime.utcnow().isoformat() + 'Z'
                listing['data_enriched'] = False
                listing['alert_sent'] = False
                
                # Save to DB
                self.listings_collection.insert_one(listing)
                print(f"   💾 Saved: {listing['symbol']} ({listing['exchange']})")
                saved_count += 1
                
            except Exception as e:
                print(f"   ❌ Error saving {listing.get('symbol')}: {e}")
        
        return saved_count
    
    async def scan_and_save(self) -> Dict:
        """
        Main method: Scan all exchanges and save results
        Returns: Summary of what was found
        """
        
        start_time = datetime.utcnow()
        
        # Run all scanners
        new_listings = await self.run_all_scanners()
        
        # Save to database
        print(f"\n💾 Saving to database...")
        saved_count = self.save_listings_to_db(new_listings)
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        summary = {
            'scan_timestamp': start_time.isoformat() + 'Z',
            'duration_seconds': round(duration, 2),
            'total_detected': len(new_listings),
            'saved_to_db': saved_count,
            'by_exchange': {}
        }
        
        # Count by exchange
        for listing in new_listings:
            exchange = listing.get('exchange', 'Unknown')
            summary['by_exchange'][exchange] = summary['by_exchange'].get(exchange, 0) + 1
        
        return summary

# CLI entry point
if __name__ == "__main__":
    import sys
    
    async def main():
        scanner = MainScanner()
        
        print("🚀 TokenScope Main Scanner")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run scan
        summary = await scanner.scan_and_save()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 SCAN SUMMARY")
        print("="*60)
        print(f"Duration: {summary['duration_seconds']}s")
        print(f"Total detected: {summary['total_detected']}")
        print(f"Saved to DB: {summary['saved_to_db']}")
        
        if summary['by_exchange']:
            print("\nBy exchange:")
            for exchange, count in summary['by_exchange'].items():
                print(f"  {exchange}: {count}")
        
        print("\n✅ Scan complete!")
    
    asyncio.run(main())
