import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from web3 import Web3
from pymongo import MongoClient
import config

class TokenAggregator:
    """
    Main class that aggregates token data from multiple sources.
    Professional trading firms call this a "Data Adapter" or "Market Data Gateway"
    """
    
    def __init__(self):
        # Connect to MongoDB
        self.mongo_client = MongoClient(config.MONGODB_URI)
        self.db = self.mongo_client['tokenscope']
        self.tokens_collection = self.db['tokens']
        
        # Create indexes for fast queries
        self.tokens_collection.create_index([('symbol', 1)])
        self.tokens_collection.create_index([('contract_address', 1)])
        self.tokens_collection.create_index([('detected_at', -1)])
        
        # Web3 connections for each chain
        self.w3_connections = {
            chain: Web3(Web3.HTTPProvider(rpc))
            for chain, rpc in config.BLOCKCHAIN_RPCS.items()
        }
        
        print("✅ TokenAggregator initialized")
    
    async def fetch_binance_listings(self) -> List[Dict]:
        """
        Fetch new listings from Binance announcements
        
        Why async? We're making 5+ API calls. Async allows them to run concurrently.
        Sync would take 5 seconds, async takes 1 second.
        """
        url = config.EXCHANGE_APIS['binance']['announcements']
        params = {
            'type': '1',
            'catalogId': '48',  # New Cryptocurrency Listing category
            'pageNo': '1',
            'pageSize': '15'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status != 200:
                        print(f"⚠️ Binance API returned {response.status}")
                        return []
                    
                    data = await response.json()
                    articles = data.get('catalogs', [{}])[0].get('articles', [])
                    
                    tokens = []
                    for article in articles:
                        # Only process recent articles (last 7 days)
                        article_date = datetime.fromtimestamp(article.get('releaseDate', 0) / 1000)
                        if datetime.now() - article_date > timedelta(days=7):
                            continue
                        
                        token = self._parse_binance_article(article)
                        if token:
                            tokens.append(token)
                    
                    print(f"✅ Found {len(tokens)} Binance listings")
                    return tokens
                    
            except Exception as e:
                print(f"❌ Error fetching Binance listings: {e}")
                return []
    
    def _parse_binance_article(self, article: Dict) -> Optional[Dict]:
        """
        Extract token information from announcement text
        
        Why separate parsing? 
        - Makes testing easier (can test parsing without API calls)
        - Can improve parsing logic without changing fetch logic
        - Follows Single Responsibility Principle
        """
        import re
        
        title = article.get('title', '')
        code = article.get('code', '')
        
        # Look for patterns like "Bitcoin (BTC)" or "Ethereum (ETH)"
        match = re.search(r'(.+?)\s*\(([A-Z]{2,10})\)', title)
        if not match:
            return None
        
        name = match.group(1).strip()
        symbol = match.group(2).strip()
        
        # Determine listing type
        listing_type = 'spot'
        if 'alpha' in title.lower():
            listing_type = 'alpha'
        elif 'futures' in title.lower() or 'perpetual' in title.lower():
            listing_type = 'futures'
        
        return {
            'name': name,
            'symbol': symbol,
            'exchange': 'Binance',
            'listing_type': listing_type,
            'announcement_url': f"https://www.binance.com/en/support/announcement/{code}",
            'detected_at': datetime.now().isoformat(),
            'data_complete': False,  # Will be enriched later
            'last_updated': datetime.now().isoformat()
        }
    
    async def fetch_pancakeswap_cakepad(self) -> List[Dict]:
        """
        Monitor PancakeSwap CAKEPAD launches
        
        Why scrape blog? PancakeSwap doesn't have public API for CAKEPAD schedule.
        Alternative: Could monitor their smart contract events on-chain.
        """
        import feedparser
        
        feed_url = config.EXCHANGE_APIS['pancakeswap']['blog_rss']
        
        try:
            feed = feedparser.parse(feed_url)
            
            tokens = []
            for entry in feed.entries[:10]:  # Check last 10 posts
                if 'cakepad' in entry.title.lower():
                    token = self._parse_pancakeswap_post(entry)
                    if token:
                        tokens.append(token)
            
            print(f"✅ Found {len(tokens)} PancakeSwap CAKEPAD listings")
            return tokens
            
        except Exception as e:
            print(f"❌ Error fetching PancakeSwap: {e}")
            return []
    
    def _parse_pancakeswap_post(self, entry) -> Optional[Dict]:
        """Parse PancakeSwap blog post for token details"""
        import re
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(entry.summary, 'html.parser')
        text = soup.get_text()
        
        # Look for contract address
        contract_match = re.search(r'0x[a-fA-F0-9]{40}', text)
        
        # Extract token name from title
        title = entry.title
        name_match = re.search(r'CAKEPAD[:\s]+(.+?)(?:\s+\(|$)', title)
        
        if not name_match:
            return None
        
        name = name_match.group(1).strip()
        
        return {
            'name': name,
            'symbol': name.upper(),  # Will be corrected during enrichment
            'exchange': 'PancakeSwap CAKEPAD',
            'listing_type': 'presale',
            'contract_address': contract_match.group(0) if contract_match else None,
            'chain': 'BSC',
            'announcement_url': entry.link,
            'detected_at': datetime.now().isoformat(),
            'data_complete': False,
            'last_updated': datetime.now().isoformat()
        }
    
    async def enrich_token_data(self, token: Dict) -> Dict:
        """
        THIS IS THE KEY FUNCTION - Called when user clicks "Generate JSON"
        
        Why separate from fetching?
        - Fetch is cheap (just scraping announcements)
        - Enrichment is expensive (blockchain calls, API limits)
        - Only enrich when user requests it (on button click)
        
        Professional trading systems call this "lazy loading" or "on-demand enrichment"
        """
        print(f"🔄 Enriching data for {token['symbol']}...")
        
        enriched = token.copy()
        
        # Step 1: Verify contract (if address exists)
        if token.get('contract_address'):
            verification = await self.verify_contract(
                token['contract_address'],
                token.get('chain', 'BSC')
            )
            enriched['verification'] = verification
        else:
            enriched['verification'] = {
                'contract_verified': False,
                'status': 'No contract address available',
                'risk_score': 50
            }
        
        # Step 2: Get price data from DEX
        if token.get('contract_address'):
            price_data = await self.get_dex_price_data(token['contract_address'])
            enriched['price_data'] = price_data
            
            # Step 3: Find where to buy
            buy_locations = await self.get_buy_locations(token['contract_address'])
            enriched['where_to_buy_now'] = buy_locations
        
        # Step 4: Get social metrics
        social = await self.get_social_metrics(token['name'], token['symbol'])
        enriched['social_metrics'] = social
        
        # Step 5: Generate AI recommendation
        recommendation = self.generate_ai_recommendation(enriched)
        enriched['ai_recommendation'] = recommendation
        
        # Mark as complete
        enriched['data_complete'] = True
        enriched['last_updated'] = datetime.now().isoformat()
        
        # Save to database
        self.tokens_collection.update_one(
            {'symbol': token['symbol'], 'exchange': token['exchange']},
            {'$set': enriched},
            upsert=True
        )
        
        print(f"✅ Enrichment complete for {token['symbol']}")
        return enriched
    
    async def verify_contract(self, address: str, chain: str) -> Dict:
        """
        Verify smart contract on blockchain explorer
        
        Why important? 
        - Verified = Source code visible = Can check for backdoors
        - Unverified = Could be honeypot or rug pull
        
        Professional audit firms check this first.
        """
        if chain == 'BSC':
            api_url = 'https://api.bscscan.com/api'
            api_key = config.BSCSCAN_API_KEY
        elif chain == 'ETH':
            api_url = 'https://api.etherscan.io/api'
            api_key = config.ETHERSCAN_API_KEY
        else:
            return {'error': f'Unsupported chain: {chain}'}
        
        verification = {
            'contract_verified': False,
            'holder_count': 0,
            'honeypot_check': 'UNKNOWN',
            'creator_address': None,
            'creation_txn': None,
            'risk_score': 50
        }
        
        async with aiohttp.ClientSession() as session:
            # Check if contract is verified
            params = {
                'module': 'contract',
                'action': 'getsourcecode',
                'address': address,
                'apikey': api_key
            }
            
            try:
                async with session.get(api_url, params=params, timeout=10) as resp:
                    data = await resp.json()
                    if data.get('status') == '1' and data['result'][0].get('SourceCode'):
                        verification['contract_verified'] = True
                        verification['contract_name'] = data['result'][0].get('ContractName')
            except Exception as e:
                print(f"⚠️ Error checking verification: {e}")
            
            # Get creator address
            params = {
                'module': 'contract',
                'action': 'getcontractcreation',
                'contractaddresses': address,
                'apikey': api_key
            }
            
            try:
                async with session.get(api_url, params=params, timeout=10) as resp:
                    data = await resp.json()
                    if data.get('status') == '1' and data.get('result'):
                        verification['creator_address'] = data['result'][0].get('contractCreator')
                        verification['creation_txn'] = data['result'][0].get('txHash')
            except Exception as e:
                print(f"⚠️ Error getting creator: {e}")
            
            # Honeypot detection (external service)
            try:
                honeypot_url = f"https://api.honeypot.is/v2/IsHoneypot"
                async with session.get(honeypot_url, params={'address': address}, timeout=10) as resp:
                    honeypot_data = await resp.json()
                    is_honeypot = honeypot_data.get('honeypotResult', {}).get('isHoneypot', False)
                    verification['honeypot_check'] = 'RISKY' if is_honeypot else 'SAFE'
            except:
                verification['honeypot_check'] = 'UNKNOWN'
        
        # Calculate risk score (0-100, lower is better)
        risk = 100
        if verification['contract_verified']:
            risk -= 30
        if verification['honeypot_check'] == 'SAFE':
            risk -= 30
        if verification['creator_address']:
            risk -= 10
        
        verification['risk_score'] = max(0, risk)
        verification['risk_level'] = 'LOW' if risk < 30 else 'MEDIUM' if risk < 60 else 'HIGH'
        
        return verification
    
    async def get_dex_price_data(self, address: str) -> Optional[Dict]:
        """
        Get live price from DEX aggregators
        
        Why DexScreener? 
        - Free API (no key needed)
        - Aggregates all DEXs (Uniswap, PancakeSwap, etc.)
        - Real-time data
        - Used by professional traders
        """
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    data = await resp.json()
                    
                    if not data.get('pairs'):
                        return None
                    
                    # Get pair with highest liquidity (most reliable price)
                    pairs = data['pairs']
                    main_pair = max(pairs, key=lambda p: float(p.get('liquidity', {}).get('usd', 0)))
                    
                    return {
                        'current_price_usd': float(main_pair.get('priceUsd', 0)),
                        'price_change_24h': float(main_pair.get('priceChange', {}).get('h24', 0)),
                        'volume_24h': float(main_pair.get('volume', {}).get('h24', 0)),
                        'liquidity_usd': float(main_pair.get('liquidity', {}).get('usd', 0)),
                        'market_cap': float(main_pair.get('marketCap', 0)),
                        'fdv': float(main_pair.get('fdv', 0)),
                        'price_change_5m': float(main_pair.get('priceChange', {}).get('m5', 0)),
                        'price_change_1h': float(main_pair.get('priceChange', {}).get('h1', 0)),
                        'price_change_6h': float(main_pair.get('priceChange', {}).get('h6', 0)),
                        'all_time_high': float(main_pair.get('priceChange', {}).get('ath', 0)),
                        'dex_id': main_pair.get('dexId'),
                        'pair_address': main_pair.get('pairAddress'),
                        'last_updated': datetime.now().isoformat()
                    }
                    
            except Exception as e:
                print(f"⚠️ Error fetching DEX price: {e}")
                return None
    
    async def get_buy_locations(self, address: str) -> List[Dict]:
        """
        Find where token can be purchased RIGHT NOW
        
        Why critical? User needs to know WHERE to buy before CEX listing.
        Professional traders call this "liquidity mapping"
        """
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    data = await resp.json()
                    
                    if not data.get('pairs'):
                        return []
                    
                    buy_locations = []
                    for pair in data['pairs']:
                        liquidity = float(pair.get('liquidity', {}).get('usd', 0))
                        
                        # Only include pairs with >$10K liquidity (avoid low-liq scams)
                        if liquidity < 10000:
                            continue
                        
                        buy_locations.append({
                            'platform': pair.get('dexId', 'Unknown DEX'),
                            'type': 'DEX',
                            'chain': pair.get('chainId', 'Unknown'),
                            'pair_address': pair.get('pairAddress'),
                            'url': pair.get('url', ''),
                            'current_price': float(pair.get('priceUsd', 0)),
                            'liquidity_usd': liquidity,
                            'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                            'pair_created_at': pair.get('pairCreatedAt'),
                            'base_token': pair.get('baseToken', {}).get('symbol'),
                            'quote_token': pair.get('quoteToken', {}).get('symbol')
                        })
                    
                    # Sort by liquidity (highest first)
                    buy_locations.sort(key=lambda x: x['liquidity_usd'], reverse=True)
                    
                    return buy_locations[:10]  # Top 10 most liquid pairs
                    
            except Exception as e:
                print(f"⚠️ Error fetching buy locations: {e}")
                return []
    
    async def get_social_metrics(self, name: str, symbol: str) -> Dict:
        """
        Get Twitter, Telegram followers
        
        Why important? Social following indicates community strength.
        Dead socials = likely rug pull
        
        Professional firms use sentiment analysis here.
        """
        # Placeholder - would need Twitter API key
        # In production, you'd:
        # 1. Search Twitter for @{symbol} or #{symbol}
        # 2. Get follower count
        # 3. Analyze sentiment of recent tweets
        # 4. Check Telegram member count via API
        
        return {
            'twitter_followers': 0,
            'telegram_members': 0,
            'discord_members': 0,
            'reddit_subscribers': 0,
            'sentiment_score': 50,  # 0-100, 50 is neutral
            'trending_rank': None,
            'note': 'Social metrics require API keys (not implemented in demo)'
        }
    
    def generate_ai_recommendation(self, token: Dict) -> Dict:
        """
        Generate trading recommendation based on all collected data
        
        This is algorithmic trading logic - similar to what hedge funds use.
        In production, this would be a ML model trained on historical pumps.
        
        For now, we use a rule-based system.
        """
        verification = token.get('verification', {})
        price_data = token.get('price_data', {})
        buy_locations = token.get('where_to_buy_now', [])
        
        # Initialize score (0-100)
        confidence = 50
        
        # Risk factors (negative indicators)
        risk_score = verification.get('risk_score', 50)
        if risk_score < 30:
            confidence += 20  # Low risk = good
        elif risk_score > 60:
            confidence -= 25  # High risk = bad
        
        # Liquidity (can you actually buy/sell?)
        total_liquidity = sum(loc.get('liquidity_usd', 0) for loc in buy_locations)
        if total_liquidity > 500000:
            confidence += 15  # High liquidity = good
        elif total_liquidity < 50000:
            confidence -= 20  # Low liquidity = risky
        
        # Volume (is there actual trading activity?)
        volume_24h = price_data.get('volume_24h', 0)
        if volume_24h > 1000000:
            confidence += 10  # High volume = interest
        elif volume_24h < 50000:
            confidence -= 10  # Low volume = no interest
        
        # Price momentum (is it pumping already?)
        price_change_24h = price_data.get('price_change_24h', 0)
        if 20 < price_change_24h < 150:
            confidence += 10  # Healthy growth
        elif price_change_24h > 300:
            confidence -= 15  # Overheated, might dump
        elif price_change_24h < -30:
            confidence -= 10  # Bleeding
        
        # Contract verification (is it safe?)
        if verification.get('contract_verified'):
            confidence += 10
        
        if verification.get('honeypot_check') == 'RISKY':
            confidence -= 30  # Huge red flag
        
        # Determine action
        if confidence > 70:
            action = 'BUY'
            reasoning = 'Strong fundamentals, good momentum, acceptable risk'
        elif confidence > 50:
            action = 'WATCH'
            reasoning = 'Mixed signals, wait for better entry or more data'
        else:
            action = 'AVOID'
            reasoning = 'High risk factors detected, insufficient liquidity, or unfavorable conditions'
        
        # Calculate price targets
        current_price = price_data.get('current_price_usd', 0)
        
        recommendation = {
            'action': action,
            'confidence': min(95, max(20, int(confidence))),
            'reasoning': reasoning,
            'suggested_entry': round(current_price * 0.98, 6) if current_price else 0,  # 2% below current
            'target_2x': round(current_price * 2.0, 6) if current_price else 0,
            'target_3x': round(current_price * 3.0, 6) if current_price else 0,
            'target_5x': round(current_price * 5.0, 6) if current_price else 0,
            'stop_loss': round(current_price * 0.80, 6) if current_price else 0,  # -20%
            'risk_reward_ratio': '1:2.5',  # Risk 20% to make 50%
            'position_size_recommendation': '3-5% of portfolio' if action == 'BUY' else '0%',
            'time_horizon': '24-72 hours' if action == 'BUY' else 'N/A',
            'key_metrics': {
                'risk_score': risk_score,
                'liquidity_score': min(100, int(total_liquidity / 10000)),
                'volume_score': min(100, int(volume_24h / 10000)),
                'momentum_score': min(100, max(0, 50 + int(price_change_24h / 2)))
            }
        }
        
        return recommendation
    
    async def scan_all_exchanges(self) -> List[Dict]:
        """
        Run a full scan of all monitored exchanges
        
        Called by GitHub Actions every 5 minutes
        Stores results in MongoDB for frontend to display
        """
        print("🔍 Starting exchange scan...")
        
        # Fetch from all exchanges concurrently
        results = await asyncio.gather(
            self.fetch_binance_listings(),
            self.fetch_pancakeswap_cakepad(),
            # Add more exchanges here
        )
        
        # Flatten results
        all_tokens = []
        for result in results:
            all_tokens.extend(result)
        
        # Save to database (without full enrichment)
        for token in all_tokens:
            self.tokens_collection.update_one(
                {'symbol': token['symbol'], 'exchange': token['exchange']},
                {'$set': token},
                upsert=True
            )
        
        print(f"✅ Scan complete. Found {len(all_tokens)} tokens")
        return all_tokens

# CLI interface for testing
if __name__ == "__main__":
    import sys
    
    aggregator = TokenAggregator()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'scan':
            # Run exchange scan
            tokens = asyncio.run(aggregator.scan_all_exchanges())
            print(f"\n📋 Found {len(tokens)} tokens:")
            for token in tokens:
                print(f"  - {token['symbol']} on {token['exchange']}")
        
        elif command == 'enrich':
            # Enrich specific token
            if len(sys.argv) < 3:
                print("Usage: python aggregator.py enrich <SYMBOL>")
                sys.exit(1)
            
            symbol = sys.argv[2]
            token = aggregator.tokens_collection.find_one({'symbol': symbol})
            
            if not token:
                print(f"❌ Token {symbol} not found in database")
                sys.exit(1)
            
            enriched = asyncio.run(aggregator.enrich_token_data(token))
            print(f"\n✅ Enriched data for {symbol}:")
            print(json.dumps(enriched, indent=2, default=str))
        
        else:
            print("Unknown command. Use: scan | enrich <SYMBOL>")
    else:
        print("Usage: python aggregator.py <scan|enrich>")

# Import AI analyzer at top of file
from ai_analyzer import analyze_token_with_ai, get_market_sentiment

# Update the generate_ai_recommendation function:
def generate_ai_recommendation_with_groq(self, token: Dict) -> Dict:
    """
    Generate AI-powered recommendation using Groq
    """
    
    # Get AI analysis
    ai_result = analyze_token_with_ai(token)
    
    # Get market sentiment
    sentiment = get_market_sentiment(token['symbol'])
    
    # Combine with algorithmic scoring
    verification = token.get('verification', {})
    price_data = token.get('price_data', {})
    
    # Calculate confidence based on data quality
    confidence = 50
    
    if verification.get('contract_verified'):
        confidence += 15
    if verification.get('honeypot_check') == 'SAFE':
        confidence += 15
    if price_data.get('volume_24h', 0) > 100000:
        confidence += 10
    if sentiment.get('sentiment') == 'BULLISH':
        confidence += 10
    
    current_price = price_data.get('current_price_usd', 0)
    
    return {
        'action': ai_result['recommendation'],
        'confidence': min(95, max(30, confidence)),
        'ai_analysis': ai_result['ai_analysis'],
        'market_sentiment': sentiment,
        'suggested_entry': round(current_price * 0.98, 6) if current_price else 0,
        'target_2x': round(current_price * 2.0, 6) if current_price else 0,
        'target_5x': round(current_price * 5.0, 6) if current_price else 0,
        'stop_loss': round(current_price * 0.80, 6) if current_price else 0,
        'position_size_recommendation': '3-5% of portfolio' if ai_result['recommendation'] == 'BUY' else '0%',
        'model': ai_result['model_used']
    }
