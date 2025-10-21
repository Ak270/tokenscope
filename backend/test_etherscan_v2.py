"""
Test Etherscan V2 API with single key across multiple chains
"""
import requests
import config

def test_single_chain(chain_name: str, test_address: str = '0xb5d85cbf7cb3ee0d56b3bb207d5fc4b82f43f511'):
    """Test a single chain using Etherscan V2 API"""
    
    chain_id = config.CHAIN_IDS.get(chain_name)
    if not chain_id:
        print(f"   ⚠️ {chain_name}: Chain ID not found")
        return False
    
    # Build V2 URL
    url = f"{config.ETHERSCAN_V2_BASE_URL}?chainid={chain_id}&module=account&action=balance&address={test_address}&tag=latest&apikey={config.ETHERSCAN_API_KEY}"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if data.get('status') == '1':
            balance = int(data.get('result', 0))
            balance_eth = balance / 1e18
            print(f"   ✅ {chain_name} (ID: {chain_id}): Balance = {balance_eth:.6f}")
            return True
        else:
            error_msg = data.get('message', 'Unknown error')
            print(f"   ❌ {chain_name} (ID: {chain_id}): {error_msg}")
            return False
            
    except Exception as e:
        print(f"   ❌ {chain_name} (ID: {chain_id}): {str(e)[:50]}")
        return False

def test_all_chains():
    """Test Etherscan V2 API across multiple chains"""
    
    print("🧪 TESTING ETHERSCAN V2 API (Single Key, Multiple Chains)\n")
    print(f"API Key: {config.ETHERSCAN_API_KEY[:10]}...{config.ETHERSCAN_API_KEY[-4:]}\n")
    
    # Test major chains
    test_chains = [
        'ETH',
        'BSC',
        'POLYGON',
        'ARBITRUM',
        'BASE',
        'OPTIMISM',
        'AVALANCHE'
    ]
    
    results = {}
    for chain in test_chains:
        results[chain] = test_single_chain(chain)
    
    print("\n" + "="*50)
    success_count = sum(results.values())
    total_count = len(results)
    print(f"✅ Success: {success_count}/{total_count} chains")
    
    if success_count == 0:
        print("\n⚠️ TROUBLESHOOTING:")
        print("1. Check your API key is correct")
        print("2. Make sure you're using an Etherscan V2 key")
        print("3. Visit: https://etherscan.io/myapikey to create/verify key")
    
    return results

if __name__ == "__main__":
    test_all_chains()
