"""
Master verification system to test all components
Tests real-world scenarios with actual tokens
"""

import asyncio
from datetime import datetime
import config
from aggregator import TokenAggregator
from ai_analyzer import analyze_token_with_ai
import json

class SystemVerifier:
    """Test all components end-to-end"""
    
    def __init__(self):
        self.aggregator = TokenAggregator()
        self.results = {
            'exchange_scanning': {},
            'contract_verification': {},
            'price_data': {},
            'ai_analysis': {},
            'enrichment': {}
        }
    
    async def verify_exchange_scanning(self):
        """Test 1: Can we detect new listings from exchanges?"""
        print("="*60)
        print("TEST 1: EXCHANGE SCANNING")
        print("="*60)
        
        # Test Binance announcements
        print("\n📡 Testing Binance API...")
        try:
            binance_tokens = await self.aggregator.fetch_binance_listings()
            
            if binance_tokens:
                print(f"✅ Binance: Found {len(binance_tokens)} listings")
                for token in binance_tokens[:3]:
                    print(f"   • {token['symbol']} - {token['name']} ({token['exchange']})")
                self.results['exchange_scanning']['binance'] = 'PASS'
            else:
                print("⚠️  Binance: No listings found (may be normal if no recent listings)")
                self.results['exchange_scanning']['binance'] = 'EMPTY'
        except Exception as e:
            print(f"❌ Binance: {e}")
            self.results['exchange_scanning']['binance'] = 'FAIL'
        
        # Test PancakeSwap CAKEPAD
        print("\n🥞 Testing PancakeSwap CAKEPAD...")
        try:
            pancake_tokens = await self.aggregator.fetch_pancakeswap_cakepad()
            
            if pancake_tokens:
                print(f"✅ PancakeSwap: Found {len(pancake_tokens)} listings")
                for token in pancake_tokens[:3]:
                    print(f"   • {token['symbol']} - {token['name']}")
                self.results['exchange_scanning']['pancakeswap'] = 'PASS'
            else:
                print("⚠️  PancakeSwap: No CAKEPAD listings found")
                self.results['exchange_scanning']['pancakeswap'] = 'EMPTY'
        except Exception as e:
            print(f"❌ PancakeSwap: {e}")
            self.results['exchange_scanning']['pancakeswap'] = 'FAIL'
    
    async def verify_contract_verification(self):
        """Test 2: Can we verify contracts and detect scams?"""
        print("\n" + "="*60)
        print("TEST 2: CONTRACT VERIFICATION")
        print("="*60)
        
        # Test with known contracts
        test_contracts = {
            'USDT (Legit)': {
                'address': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
                'chain': 'ETH',
                'expected': 'verified'
            },
            'PancakeSwap (Legit)': {
                'address': '0x10ED43C718714eb63d5aA57B78B54704E256024E',
                'chain': 'BSC',
                'expected': 'verified'
            }
        }
        
        for name, contract_info in test_contracts.items():
            print(f"\n🔍 Testing: {name}")
            try:
                verification = await self.aggregator.verify_contract(
                    contract_info['address'],
                    contract_info['chain']
                )
                
                print(f"   Contract Verified: {verification.get('contract_verified')}")
                print(f"   Honeypot Check: {verification.get('honeypot_check')}")
                print(f"   Risk Score: {verification.get('risk_score')}/100")
                print(f"   Risk Level: {verification.get('risk_level')}")
                
                if verification.get('contract_verified'):
                    print(f"   ✅ Successfully verified {name}")
                    self.results['contract_verification'][name] = 'PASS'
                else:
                    print(f"   ⚠️  Could not verify {name}")
                    self.results['contract_verification'][name] = 'PARTIAL'
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.results['contract_verification'][name] = 'FAIL'
    
    async def verify_price_data(self):
        """Test 3: Can we fetch accurate price data?"""
        print("\n" + "="*60)
        print("TEST 3: PRICE DATA FETCHING")
        print("="*60)
        
        # Test with popular tokens that have DEX liquidity
        test_tokens = {
            'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
            'USDC': '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
            'PancakeSwap': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82'
        }
        
        for token_name, address in test_tokens.items():
            print(f"\n💰 Testing: {token_name}")
            try:
                price_data = await self.aggregator.get_dex_price_data(address)
                
                if price_data:
                    print(f"   Current Price: ${price_data.get('current_price_usd')}")
                    print(f"   24h Volume: ${price_data.get('volume_24h'):,.0f}")
                    print(f"   Liquidity: ${price_data.get('liquidity_usd'):,.0f}")
                    print(f"   24h Change: {price_data.get('price_change_24h')}%")
                    print(f"   ✅ Price data retrieved successfully")
                    self.results['price_data'][token_name] = 'PASS'
                else:
                    print(f"   ⚠️  No price data found (may not be on DEX)")
                    self.results['price_data'][token_name] = 'EMPTY'
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
                self.results['price_data'][token_name] = 'FAIL'
    
    async def verify_ai_analysis(self):
        """Test 4: Is AI analysis working correctly?"""
        print("\n" + "="*60)
        print("TEST 4: AI ANALYSIS")
        print("="*60)
        
        test_token = {
            'name': 'SigmaDotMoney',
            'symbol': 'SIGMA',
            'exchange': 'Binance Alpha',
            'chain': 'BSC',
            'verification': {
                'contract_verified': True,
                'honeypot_check': 'SAFE',
                'risk_score': 25
            },
            'price_data': {
                'current_price_usd': 0.038,
                'volume_24h': 1500000,
                'liquidity_usd': 450000,
                'price_change_24h': 280
            }
        }
        
        print("\n🤖 Testing Groq AI with sample token...")
        try:
            result = analyze_token_with_ai(test_token)
            
            if result.get('ai_analysis') and 'unavailable' not in result['ai_analysis'].lower():
                print(f"   ✅ AI Analysis Generated:")
                print(f"\n{result['ai_analysis'][:300]}...")
                print(f"\n   Recommendation: {result['recommendation']}")
                print(f"   Model: {result.get('model_used', 'Unknown')}")
                self.results['ai_analysis']['groq'] = 'PASS'
            else:
                print(f"   ⚠️  AI returned: {result.get('ai_analysis')}")
                self.results['ai_analysis']['groq'] = 'FAIL'
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            self.results['ai_analysis']['groq'] = 'FAIL'
    
    async def verify_full_enrichment(self):
        """Test 5: Full end-to-end enrichment"""
        print("\n" + "="*60)
        print("TEST 5: FULL TOKEN ENRICHMENT")
        print("="*60)
        
        # Use a real token with contract
        test_token = {
            'name': 'PancakeSwap Token',
            'symbol': 'CAKE',
            'exchange': 'Test',
            'contract_address': '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
            'chain': 'BSC',
            'detected_at': datetime.now().isoformat(),
            'data_complete': False
        }
        
        print(f"\n🔄 Enriching: {test_token['name']} ({test_token['symbol']})")
        
        try:
            enriched = await self.aggregator.enrich_token_data(test_token)
            
            # Check what data we got
            checks = {
                'Verification Data': bool(enriched.get('verification')),
                'Price Data': bool(enriched.get('price_data')),
                'Buy Locations': bool(enriched.get('where_to_buy_now')),
                'AI Recommendation': bool(enriched.get('ai_recommendation')),
                'Data Complete Flag': enriched.get('data_complete', False)
            }
            
            print("\n   Enrichment Results:")
            for check, passed in checks.items():
                status = "✅" if passed else "❌"
                print(f"   {status} {check}")
            
            # Show sample of enriched data
            if enriched.get('price_data'):
                print(f"\n   Price: ${enriched['price_data'].get('current_price_usd')}")
                print(f"   Volume: ${enriched['price_data'].get('volume_24h'):,.0f}")
            
            if enriched.get('ai_recommendation'):
                print(f"\n   AI Action: {enriched['ai_recommendation'].get('action')}")
                print(f"   Confidence: {enriched['ai_recommendation'].get('confidence')}%")
            
            if all(checks.values()):
                print("\n   ✅ FULL ENRICHMENT SUCCESSFUL")
                self.results['enrichment']['full'] = 'PASS'
            else:
                print("\n   ⚠️  PARTIAL ENRICHMENT")
                self.results['enrichment']['full'] = 'PARTIAL'
                
        except Exception as e:
            print(f"\n   ❌ Enrichment failed: {e}")
            self.results['enrichment']['full'] = 'FAIL'
    
    def print_summary(self):
        """Print final test summary"""
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.results.items():
            print(f"\n📊 {category.upper().replace('_', ' ')}:")
            for test_name, result in tests.items():
                total_tests += 1
                if result == 'PASS':
                    passed_tests += 1
                    emoji = "✅"
                elif result == 'PARTIAL':
                    emoji = "⚠️"
                elif result == 'EMPTY':
                    emoji = "⭕"
                else:
                    emoji = "❌"
                
                print(f"   {emoji} {test_name}: {result}")
        
        print("\n" + "="*60)
        score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"OVERALL SCORE: {passed_tests}/{total_tests} ({score:.0f}%)")
        print("="*60)
        
        if score >= 80:
            print("\n🎉 SYSTEM IS PRODUCTION READY!")
        elif score >= 60:
            print("\n⚠️  SYSTEM NEEDS MINOR FIXES")
        else:
            print("\n❌ SYSTEM NEEDS MAJOR FIXES")
        
        return score

async def run_full_verification():
    """Run all verification tests"""
    print("\n" + "🔬 TOKENSCOPE SYSTEM VERIFICATION 🔬".center(60))
    print("Testing all components with real data\n")
    
    verifier = SystemVerifier()
    
    # Run all tests
    await verifier.verify_exchange_scanning()
    await verifier.verify_contract_verification()
    await verifier.verify_price_data()
    await verifier.verify_ai_analysis()
    await verifier.verify_full_enrichment()
    
    # Print summary
    score = verifier.print_summary()
    
    # Save report
    report_file = f"verification_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'score': score,
            'results': verifier.results
        }, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_file}")
    
    return score

if __name__ == "__main__":
    score = asyncio.run(run_full_verification())
    exit(0 if score >= 80 else 1)
