"""
Abstract base class for all exchange scanners
Enforces consistent interface across exchanges
"""

from abc import ABC, abstractmethod
from typing import List, Dict
import asyncio
import aiohttp
from datetime import datetime

class BaseScanner(ABC):
    """Base scanner all exchange scanners must implement"""
    
    def __init__(self, exchange_name: str):
        self.exchange_name = exchange_name
        self.session = None
        self.last_scan_pairs = set()  # Track what we've seen
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def fetch_all_pairs(self) -> List[str]:
        """
        Fetch all trading pairs from exchange
        Returns: ['BTC_USDT', 'ETH_USDT', ...]
        """
        pass
    
    @abstractmethod
    async def get_pair_details(self, pair: str) -> Dict:
        """
        Get detailed info for a specific pair
        Returns: {symbol, price, volume, etc}
        """
        pass
    
    async def detect_new_listings(self) -> List[Dict]:
        """
        Core logic: Compare current pairs with last scan
        Returns: List of newly detected pairs with full details
        """
        
        current_pairs = await self.fetch_all_pairs()
        current_set = set(current_pairs)
        
        # Find new pairs
        new_pairs = current_set - self.last_scan_pairs
        
        if not new_pairs:
            print(f"[{self.exchange_name}] No new listings")
            return []
        
        print(f"[{self.exchange_name}] 🆕 Found {len(new_pairs)} new pairs: {new_pairs}")
        
        # Get details for each new pair
        new_listings = []
        for pair in new_pairs:
            try:
                details = await self.get_pair_details(pair)
                if details:
                    details['exchange'] = self.exchange_name
                    details['detected_at'] = datetime.utcnow().isoformat() + 'Z'
                    new_listings.append(details)
            except Exception as e:
                print(f"Error getting details for {pair}: {e}")
        
        # Update our memory
        self.last_scan_pairs = current_set
        
        return new_listings
    
    async def scan(self) -> List[Dict]:
        """
        Public method to run a scan
        """
        try:
            return await self.detect_new_listings()
        except Exception as e:
            print(f"[{self.exchange_name}] Scan failed: {e}")
            return []
