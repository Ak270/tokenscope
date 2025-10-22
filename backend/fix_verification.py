"""
Fixed contract verification using Etherscan V2 API
"""

import requests
import config

def verify_contract_v2(contract_address: str, chain: str = 'ETH') -> dict:
    """
    Verify contract using Etherscan V2 API
    
    Args:
        contract_address: Contract address to verify
        chain: Blockchain (ETH, BSC, POLYGON, etc.)
    
    Returns:
        dict with verification results
    """
    
    # Get chain ID
    chain_id = config.CHAIN_IDS.get(chain.upper())
    if not chain_id:
        return {
            'contract_verified': False,
            'error': f'Unsupported chain: {chain}'
        }
    
    # Build V2 API URL
    url = f"{config.ETHERSCAN_V2_BASE_URL}"
    params = {
        'chainid': chain_id,
        'module': 'contract',
        'action': 'getsourcecode',
        'address': contract_address,
        'apikey': config.ETHERSCAN_API_KEY
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == '1' and data.get('result'):
            result = data['result'][0]
            
            is_verified = result.get('SourceCode') != ''
            contract_name = result.get('ContractName', 'Unknown')
            compiler = result.get('CompilerVersion', 'Unknown')
            
            return {
                'contract_verified': is_verified,
                'contract_name': contract_name,
                'compiler_version': compiler,
                'source_code_available': is_verified,
                'abi': result.get('ABI', ''),
                'constructor_args': result.get('ConstructorArguments', ''),
                'optimization_used': result.get('OptimizationUsed') == '1',
                'proxy': result.get('Proxy') == '1',
                'implementation': result.get('Implementation', '')
            }
        else:
            return {
                'contract_verified': False,
                'error': data.get('message', 'Unknown error')
            }
            
    except Exception as e:
        return {
            'contract_verified': False,
            'error': str(e)
        }

# Test it
if __name__ == "__main__":
    print("🧪 Testing Contract Verification V2\n")
    
    test_contracts = {
        'USDT on Ethereum': ('0xdAC17F958D2ee523a2206206994597C13D831ec7', 'ETH'),
        'PancakeSwap on BSC': ('0x10ED43C718714eb63d5aA57B78B54704E256024E', 'BSC'),
        'USDC on Polygon': ('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174', 'POLYGON')
    }
    
    for name, (address, chain) in test_contracts.items():
        print(f"🔍 Testing: {name}")
        result = verify_contract_v2(address, chain)
        
        print(f"   Verified: {result.get('contract_verified')}")
        if result.get('contract_verified'):
            print(f"   Name: {result.get('contract_name')}")
            print(f"   Compiler: {result.get('compiler_version')}")
            print(f"   ✅ SUCCESS")
        else:
            print(f"   Error: {result.get('error')}")
            print(f"   ❌ FAILED")
        print()
