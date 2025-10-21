"""
AI-Powered Token Analysis using Groq (FREE!)
Updated for Llama 3.3 70B Versatile (Latest Model)
"""

import json
from groq import Groq
import config

client = Groq(api_key=config.GROQ_API_KEY) if config.GROQ_API_KEY else None

def analyze_token_with_ai(token_data: dict) -> dict:
    """
    Use Groq's Llama 3.3 70B to analyze token
    FREE - No rate limits during beta!
    """
    
    if not client:
        return {
            'ai_analysis': 'AI analysis unavailable - no API key',
            'recommendation': 'MANUAL_REVIEW'
        }
    
    # Prepare data for AI
    verification = token_data.get('verification', {})
    price_data = token_data.get('price_data', {})
    
    analysis_prompt = f"""You are a professional cryptocurrency trader analyzing a new token listing.

TOKEN DATA:
Name: {token_data.get('name')}
Symbol: {token_data.get('symbol')}
Exchange: {token_data.get('exchange')}
Chain: {token_data.get('chain', 'Unknown')}

SECURITY:
Contract Verified: {verification.get('contract_verified', False)}
Honeypot Check: {verification.get('honeypot_check', 'UNKNOWN')}
Risk Score: {verification.get('risk_score', 'N/A')}/100

MARKET DATA:
Current Price: ${price_data.get('current_price_usd', 'N/A')}
24h Volume: ${price_data.get('volume_24h', 'N/A'):,.0f}
Liquidity: ${price_data.get('liquidity_usd', 'N/A'):,.0f}
24h Change: {price_data.get('price_change_24h', 'N/A')}%

Provide a concise analysis (150-200 words):
1. Risk Level (LOW/MEDIUM/HIGH)
2. Recommendation (BUY/WAIT/AVOID)
3. Key reasons (2-3 bullets)
4. Red flags (if any)
5. Position size (% of portfolio)

Be direct and actionable."""

    try:
        completion = client.chat.completions.create(
            model=config.AI_MODELS['groq']['model'],
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert crypto analyst with 10 years experience. Be concise, direct, honest about risks. Format with clear headers."
                },
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ],
            temperature=config.AI_MODELS['groq']['temperature'],
            max_tokens=config.AI_MODELS['groq']['max_tokens'],
        )
        
        ai_response = completion.choices[0].message.content
        
        # Parse recommendation
        recommendation = 'WAIT'
        if 'BUY' in ai_response.upper() and 'AVOID' not in ai_response.upper():
            recommendation = 'BUY'
        elif 'AVOID' in ai_response.upper():
            recommendation = 'AVOID'
        
        return {
            'ai_analysis': ai_response,
            'recommendation': recommendation,
            'model_used': 'Groq Llama 3.3 70B',
            'tokens_used': completion.usage.total_tokens if hasattr(completion, 'usage') else 0
        }
        
    except Exception as e:
        print(f"⚠️ AI analysis error: {e}")
        return {
            'ai_analysis': f'AI temporarily unavailable. Algorithmic analysis active.',
            'recommendation': 'MANUAL_REVIEW',
            'error': str(e)
        }

def get_market_sentiment(symbol: str) -> dict:
    """
    Get market sentiment using CoinGecko trending data
    """
    
    if not config.COINGECKO_API_KEY:
        return {'sentiment': 'NEUTRAL', 'note': 'CoinGecko API not configured'}
    
    try:
        import requests
        
        url = 'https://api.coingecko.com/api/v3/search/trending'
        headers = {'x-cg-demo-api-key': config.COINGECKO_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return {'sentiment': 'NEUTRAL', 'note': 'CoinGecko API error'}
        
        data = response.json()
        
        # Check if token is trending
        trending_coins = [coin['item']['symbol'].upper() for coin in data.get('coins', [])]
        
        if symbol.upper() in trending_coins:
            rank = trending_coins.index(symbol.upper()) + 1
            return {
                'sentiment': 'BULLISH',
                'reason': f'Trending #{rank} on CoinGecko',
                'rank': rank
            }
        else:
            return {
                'sentiment': 'NEUTRAL',
                'reason': 'Not in top trending tokens'
            }
            
    except Exception as e:
        return {'sentiment': 'UNKNOWN', 'error': str(e)}

# Test function
if __name__ == "__main__":
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
    
    result = analyze_token_with_ai(test_token)
    print('🤖 AI Analysis:')
    print(result['ai_analysis'])
    print('\n📊 Recommendation:', result['recommendation'])
    print('🔧 Model:', result.get('model_used'))
