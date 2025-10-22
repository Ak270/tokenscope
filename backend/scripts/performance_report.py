"""
Generate daily performance report
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import os

def generate_report():
    client = MongoClient(os.getenv('MONGODB_URI'))
    db = client['tokenscope']
    
    # Count listings in last 24h
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
    recent_listings = db.listings.count_documents({'detected_at': {'$gte': yesterday}})
    
    # Count opportunities
    opportunities = db.opportunities.count_documents({})
    
    # Count alerts sent
    alerts_sent = db.opportunities.count_documents({'alert_sent': True})
    
    # Count by exchange
    exchanges = db.listings.distinct('exchange')
    
    print('=' * 60)
    print('📊 DAILY PERFORMANCE REPORT')
    print('=' * 60)
    print(f'Date: {datetime.utcnow().strftime("%Y-%m-%d")}')
    print()
    print(f'📈 New listings (24h): {recent_listings}')
    print(f'🎯 Total opportunities: {opportunities}')
    print(f'📤 Alerts sent: {alerts_sent}')
    print()
    print('By Exchange:')
    for exchange in exchanges:
        count = db.listings.count_documents({'exchange': exchange})
        print(f'  {exchange}: {count}')
    print('=' * 60)
    
    client.close()

if __name__ == "__main__":
    generate_report()
