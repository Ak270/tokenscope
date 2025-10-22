"""
Binance Scanner - Refactored to use BaseScanner
Monitors Binance announcements for new listings
"""

import aiohttp
from typing import List, Dict
from datetime import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

class BinanceScanner:
    """
    Scanner for Binance exchange announcements
    Note: This is different from other scanners as it monitors announcements, not pairs
    """
    
    def __init__(self):
        self.exchange_name = 'Binance'
        self.session = None
        self.seen_announcements = set()  # Track announcement IDs
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scan(self) -> List[Dict]:
        """
        Scan Binance announcements for new listings
        """
        
        url = 'https://www.binance.com/bapi/composite/v1/public/cms/article/list/query'
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept': 'application/json',
        }
        
        params = {
            'type': 1,
            'catalogId': 48,  # New Cryptocurrency Listing
            'pageNo': 1,
            'pageSize': 20
        }
        
        try:
            async with self.session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status != 200:
                    print(f"[Binance] API error: {response.status}")
                    return []
                
                data = await response.json()
                
                if data.get('code') != '000000':
                    print(f"[Binance] API error: {data.get('message')}")
                    return []
                
                # Extract articles
                catalogs = data.get('data', {}).get('catalogs', [])
                if not catalogs:
                    return []
                
                articles = catalogs[0].get('articles', [])
                
                new_listings = []
                
                for article in articles:
                    article_id = article.get('id')
                    
                    # Skip if we've seen this announcement
                    if article_id in self.seen_announcements:
                        continue
                    
                    self.seen_announcements.add(article_id)
                    
                    title = article.get('title', '')
                    code = article.get('code', '')
                    release_date = article.get('releaseDate', 0)
                    
                    # Parse token symbols from title
                    # Example: "Binance Will List Turtle (TURTLE)"
                    symbols = self._extract_symbols_from_title(title)
                    
                    if symbols:
                        for symbol in symbols:
                            listing = {
                                'symbol': symbol,
                                'name': self._extract_name_from_title(title),
                                'exchange': 'Binance',
                                'announcement_title': title,
                                'announcement_url': f'https://www.binance.com/en/support/announcement/detail/{code}',
                                'detected_at': datetime.utcnow().isoformat() + 'Z',
                                'announcement_date': datetime.fromtimestamp(release_date / 1000).isoformat() + 'Z',
                                'listing_type': self._determine_listing_type(title)
                            }
                            new_listings.append(listing)
                
                if new_listings:
                    print(f"[Binance] Found {len(new_listings)} new announcements")
                
                return new_listings
                
        except Exception as e:
            print(f"[Binance] Scan error: {e}")
            return []
    
    def _extract_symbols_from_title(self, title: str) -> List[str]:
        """Extract token symbols from announcement title"""
        import re
        
        # Pattern: (SYMBOL) or (SYMBOL1, SYMBOL2)
        matches = re.findall(r'\(([A-Z0-9, ]+)\)', title)
        
        symbols = []
        for match in matches:
            # Split by comma if multiple symbols
            for symbol in match.split(','):
                symbol = symbol.strip()
                if len(symbol) >= 2 and len(symbol) <= 10:
                    symbols.append(symbol)
        
        return symbols
    
    def _extract_name_from_title(self, title: str) -> str:
        """Extract token name from title"""
        # Extract text before first parenthesis
        import re
        match = re.search(r'^[^(]+', title)
        if match:
            name = match.group().strip()
            # Remove common prefixes
            for prefix in ['Binance Will List ', 'Introducing ', 'Binance Will Add ']:
                name = name.replace(prefix, '')
            return name.strip()
        return ''
    
    def _determine_listing_type(self, title: str) -> str:
        """Determine listing type from title"""
        title_lower = title.lower()
        
        if 'alpha' in title_lower:
            return 'Binance Alpha'
        elif 'futures' in title_lower:
            return 'Binance Futures'
        elif 'hodler' in title_lower or 'airdrop' in title_lower:
            return 'HODLer Airdrop'
        elif 'launchpad' in title_lower or 'launchpool' in title_lower:
            return 'Launchpad'
        else:
            return 'Spot Listing'

# Test
if __name__ == "__main__":
    import asyncio
    
    async def test():
        print("🔍 Testing Binance scanner...")
        
        async with BinanceScanner() as scanner:
            result = await scanner.scan()
            print(f"\nFound {len(result)} announcements")
            
            for listing in result[:3]:
                print(f"\n  {listing['symbol']} - {listing['name']}")
                print(f"  Type: {listing['listing_type']}")
                print(f"  URL: {listing['announcement_url']}")
    
    asyncio.run(test())
