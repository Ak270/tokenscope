from pymongo import MongoClient
from datetime import datetime
import config

client = MongoClient(config.MONGODB_URI)
db = client['tokenscope']
collection = db['tokens']

# Clear existing data
collection.delete_many({})

# Add test tokens (including SIGMA-like example)
test_tokens = [
    {
        'name': 'SigmaDotMoney',
        'symbol': 'SIGMA',
        'exchange': 'Binance Alpha',
        'listing_type': 'alpha',
        'contract_address': '0x85375d3e9c4a39350f1140280a8b0de6890a40e7',
        'chain': 'BSC',
        'announcement_url': 'https://www.binance.com/en/support/announcement/sigma',
        'detected_at': datetime.now().isoformat(),
        'data_complete': False,
        'last_updated': datetime.now().isoformat()
    },
    {
        'name': 'BluWhale AI',
        'symbol': 'BLUAI',
        'exchange': 'Binance Futures',
        'listing_type': 'futures',
        'contract_address': '0x1234567890123456789012345678901234567890',
        'chain': 'ETH',
        'announcement_url': 'https://www.binance.com/en/support/announcement/bluai',
        'detected_at': datetime.now().isoformat(),
        'data_complete': False,
        'last_updated': datetime.now().isoformat()
    },
    {
        'name': 'Test Token',
        'symbol': 'TEST',
        'exchange': 'PancakeSwap CAKEPAD',
        'listing_type': 'presale',
        'contract_address': '0xabcdefabcdefabcdefabcdefabcdefabcdefabcd',
        'chain': 'BSC',
        'announcement_url': 'https://pancakeswap.finance/cakepad',
        'detected_at': datetime.now().isoformat(),
        'data_complete': False,
        'last_updated': datetime.now().isoformat()
    }
]

# Insert test data
result = collection.insert_many(test_tokens)
print(f"✅ Inserted {len(result.inserted_ids)} test tokens")

# Verify
count = collection.count_documents({})
print(f"✅ Total tokens in database: {count}")

# Show tokens
for token in collection.find():
    print(f"  - {token['symbol']} on {token['exchange']}")

client.close()
