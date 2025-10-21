import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
#  DATABASE
# ============================================
MONGODB_URI = os.getenv('MONGODB_URI')

# ============================================
#  ETHERSCAN V2 API (Single Key, All Chains!)
# ============================================
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY')

# Optional: Legacy BSCScan key (fallback)
BSCSCAN_API_KEY = os.getenv('BSCSCAN_API_KEY')

# ============================================
#  CHAIN IDs (Etherscan V2 Format)
# ============================================
CHAIN_IDS = {
    'ETH': 1,
    'SEPOLIA': 11155111,
    'HOLESKY': 17000,
    'BSC': 56,
    'BSC_TESTNET': 97,
    'POLYGON': 137,
    'AMOY': 80002,
    'ARBITRUM': 42161,
    'ARBITRUM_SEPOLIA': 421614,
    'BASE': 8453,
    'BASE_SEPOLIA': 84532,
    'OPTIMISM': 10,
    'OPTIMISM_SEPOLIA': 11155420,
    'AVALANCHE': 43114,
    'AVALANCHE_FUJI': 43113,
    'GNOSIS': 100,
    'FANTOM': 250,
    'CELO': 42220,
    'MOONBEAM': 1284,
    'MOONRIVER': 1285,
    'KROMA': 255,
    'LINEA': 59144,
    'SCROLL': 534352,
    'ZKSYNC': 324,
    'BLAST': 81457,
    'FRAXTAL': 252,
    'OPBNB': 204
}

# ============================================
#  EXPLORER API ENDPOINTS (V2 Format)
# ============================================
ETHERSCAN_V2_BASE_URL = 'https://api.etherscan.io/v2/api'

# Legacy format (fallback for BSCScan if needed)
LEGACY_EXPLORER_APIS = {
    'BSC': {
        'url': 'https://api.bscscan.com/api',
        'key': BSCSCAN_API_KEY or ETHERSCAN_API_KEY
    }
}

# ============================================
#  PRICE & MARKET DATA
# ============================================
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY')

# ============================================
#  AI ANALYSIS
# ============================================
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# ============================================
#  BLOCKCHAIN RPC ENDPOINTS
# ============================================
BLOCKCHAIN_RPCS = {
    'BSC': os.getenv('PUBLIC_BSC_RPC', 'https://bsc-dataseed1.binance.org'),
    'ETH': os.getenv('ALCHEMY_ETH_RPC', 'https://eth.llamarpc.com'),
    'POLYGON': os.getenv('ALCHEMY_POLYGON_RPC', 'https://polygon-rpc.com'),
    'ARBITRUM': os.getenv('ALCHEMY_ARBITRUM_RPC', 'https://arb1.arbitrum.io/rpc'),
    'BASE': os.getenv('ALCHEMY_BASE_RPC', 'https://mainnet.base.org'),
    'AVALANCHE': os.getenv('PUBLIC_AVAX_RPC', 'https://api.avax.network/ext/bc/C/rpc'),
    'OPTIMISM': os.getenv('PUBLIC_OPTIMISM_RPC', 'https://mainnet.optimism.io'),
}

# ============================================
#  EXCHANGE APIS
# ============================================
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
    },
    'coingecko': {
        'new_listings': 'https://api.coingecko.com/api/v3/coins/list/new',
        'trending': 'https://api.coingecko.com/api/v3/search/trending'
    }
}

# ============================================
#  CACHE & RATE LIMITS
# ============================================
CACHE_TTL = 300  # 5 minutes
RATE_LIMIT_PER_MINUTE = 60

# ============================================
#  AI MODELS
# ============================================
AI_MODELS = {
    'groq': {
        'model': 'llama-3.3-70b-versatile',
        'max_tokens': 2048,
        'temperature': 0.3
    }
}

# ============================================
#  HELPER FUNCTIONS
# ============================================
def get_explorer_url(chain: str, params: dict) -> str:
    """
    Get Etherscan V2 API URL with chainid parameter
    
    Example:
        get_explorer_url('ETH', {'module': 'account', 'action': 'balance', 'address': '0x...'})
        Returns: https://api.etherscan.io/v2/api?chainid=1&module=account&action=balance...
    """
    chain_id = CHAIN_IDS.get(chain.upper())
    if not chain_id:
        raise ValueError(f"Unsupported chain: {chain}")
    
    # Build query parameters
    query_params = {
        'chainid': chain_id,
        'apikey': ETHERSCAN_API_KEY,
        **params
    }
    
    # Convert to URL format
    query_string = '&'.join([f"{k}={v}" for k, v in query_params.items()])
    
    return f"{ETHERSCAN_V2_BASE_URL}?{query_string}"
