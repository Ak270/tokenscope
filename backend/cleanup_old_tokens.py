"""
Clean up old token data from MongoDB
Removes tokens older than specified days
"""

from pymongo import MongoClient
from datetime import datetime, timedelta
import config

def cleanup_old_tokens(days_old: int = 30):
    """
    Remove tokens older than X days
    
    Args:
        days_old: Number of days to keep (default: 30)
    """
    
    client = MongoClient(config.MONGODB_URI)
    db = client['tokenscope']
    collection = db['tokens']
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days_old)
    cutoff_iso = cutoff_date.isoformat()
    
    print(f"🗑️  Cleaning tokens older than {days_old} days...")
    print(f"📅 Cutoff date: {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Count before
    total_before = collection.count_documents({})
    print(f"📊 Total tokens before: {total_before}")
    
    # Find old tokens
    old_tokens = collection.find({
        'detected_at': {'$lt': cutoff_iso}
    })
    
    old_tokens_list = list(old_tokens)
    old_count = len(old_tokens_list)
    
    print(f"🔍 Found {old_count} tokens older than {days_old} days:")
    
    # Show what will be deleted
    for token in old_tokens_list[:10]:  # Show first 10
        detected = datetime.fromisoformat(token['detected_at'])
        age_days = (datetime.now() - detected).days
        print(f"  • {token['symbol']} - {token['name']} ({age_days} days old)")
    
    if old_count > 10:
        print(f"  ... and {old_count - 10} more")
    
    # Confirm deletion
    if old_count == 0:
        print("\n✅ No old tokens to delete!")
        client.close()
        return
    
    print(f"\n⚠️  About to delete {old_count} tokens!")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm != 'DELETE':
        print("❌ Cancelled. No data deleted.")
        client.close()
        return
    
    # Delete old tokens
    result = collection.delete_many({
        'detected_at': {'$lt': cutoff_iso}
    })
    
    # Count after
    total_after = collection.count_documents({})
    
    print(f"\n✅ Deleted {result.deleted_count} tokens")
    print(f"📊 Total tokens remaining: {total_after}")
    
    client.close()

if __name__ == "__main__":
    import sys
    
    # Allow custom days as argument
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    
    cleanup_old_tokens(days)
