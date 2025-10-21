import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
BSCSCAN_API_KEY = os.getenv('BSCSCAN_API_KEY')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')
TWITTER_BEARER_TOKEN = os.getenv('TWITTER_BEARER_TOKEN')

# Database
MONGODB_URI = os.getenv('MONGODB_URI')
REDIS_URL = os.getenv('REDIS_URL')

# Exchange APIs
EXCHANGE_APIS = {
    'binance': {
        'announcements': 'https://www.binance.com/bapi/composite/v1/public/cms/article/list/query',
        'check_interval': 60
    },
    'kucoin': {
        'announcements': 'https://www.kucoin.com/_api/cms/articles',
        'check_interval': 60
    },
    'pancakeswap': {
        'blog_rss': 'https://blog.pancakeswap.finance/feed',
        'check_interval': 300
    }
}

# Blockchain RPCs (Free public nodes)
BLOCKCHAIN_RPCS = {
    'BSC': 'https://bsc-dataseed1.binance.org',
    'ETH': 'https://eth.llamarpc.com',
    'POLYGON': 'https://polygon-rpc.com',
    'BASE': 'https://mainnet.base.org',
    'ARBITRUM': 'https://arb1.arbitrum.io/rpc'
}

# Cache TTL (Time To Live)
CACHE_TTL = 300  # 5 minutes

# Rate Limits
RATE_LIMIT_PER_MINUTE = 60
