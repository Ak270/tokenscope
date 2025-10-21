"""
Test all API keys and connections (Updated for V2)
"""
import os
from dotenv import load_dotenv
import requests
from pymongo import MongoClient
from groq import Groq
import config

load_dotenv()

print("🧪 TESTING ALL API CONNECTIONS (Etherscan V2)\n")

# 1. MongoDB
print("1️⃣ Testing MongoDB...")
try:
    client = MongoClient(os.getenv('MONGODB_URI'), serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    print("   ✅ MongoDB: Connected")
    print(f"   📊 Databases: {client.list_database_names()[:3]}")
except Exception as e:
    print(f"   ❌ MongoDB: {e}")

# 2. Etherscan V2 API (Single Key, Multiple Chains)
print("\n2️⃣ Testing Etherscan V2 API (Multichain)...")

test_chains = ['ETH', 'BSC', 'POLYGON', 'ARBITRUM', 'BASE']
test_address = '0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511'

for chain_name in test_chains:
    chain_id = config.CHAIN_IDS.get(chain_name)
    if not chain_id:
        print(f"   ⚠️ {chain_name}: Not configured")
        continue
    
    url = f"{config.ETHERSCAN_V2_BASE_URL}?chainid={chain_id}&module=account&action=balance&address={test_address}&tag=latest&apikey={config.ETHERSCAN_API_KEY}"
    
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        
        if data.get('status') == '1':
            print(f"   ✅ {chain_name} (chainid={chain_id}): Working")
        else:
            print(f"   ❌ {chain_name}: {data.get('message', 'Error')}")
    except Exception as e:
        print(f"   ❌ {chain_name}: {str(e)[:50]}")

# 3. CoinGecko
print("\n3️⃣ Testing CoinGecko API...")
cg_key = os.getenv('COINGECKO_API_KEY')
if cg_key:
    try:
        r = requests.get('https://api.coingecko.com/api/v3/ping', 
                        headers={'x-cg-demo-api-key': cg_key}, timeout=5)
        if r.status_code == 200:
            print(f"   ✅ CoinGecko: Working")
        else:
            print(f"   ❌ CoinGecko: Status {r.status_code}")
    except Exception as e:
        print(f"   ❌ CoinGecko: {e}")
else:
    print("   ⚠️ CoinGecko: No API key")

# 4. Groq AI
print("\n4️⃣ Testing Groq AI...")
groq_key = os.getenv('GROQ_API_KEY')
if groq_key:
    try:
        client = Groq(api_key=groq_key)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=10
        )
        print(f"   ✅ Groq AI: Working (Model: llama-3.3-70b-versatile)")
        print(f"   📊 Response: {completion.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ Groq AI: {e}")
else:
    print("   ⚠️ Groq AI: No API key")

# 5. DexScreener
print("\n5️⃣ Testing DexScreener...")
try:
    r = requests.get('https://api.dexscreener.com/latest/dex/tokens/0x2260fac5e5542a773aa44fbcfedf7c193bc2c599', timeout=5)
    if r.status_code == 200:
        print(f"   ✅ DexScreener: Working (no key needed)")
    else:
        print(f"   ❌ DexScreener: Status {r.status_code}")
except Exception as e:
    print(f"   ❌ DexScreener: {e}")

print("\n🎉 TEST COMPLETE!")
print("\n💡 TIP: Etherscan V2 uses ONE key for ALL chains!")
print(f"   Your key: {config.ETHERSCAN_API_KEY[:10]}...{config.ETHERSCAN_API_KEY[-4:]}")
