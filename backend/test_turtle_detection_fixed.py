"""
Fixed parser for Binance announcements
"""

import asyncio
import aiohttp

async def test_binance_api():
    """Check if we can see the TURTLE announcement"""

    params = {
        "type": 1,
        "catalogId": 48,
        "pageNo": 1,
        "pageSize": 20
    }

    url = "https://www.binance.com/bapi/composite/v1/public/cms/article/list/query"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://www.binance.com/en/support/announcement",
        "Origin": "https://www.binance.com",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, params=params) as response:
            print(f"🔍 Response status: {response.status}")
            
            if response.status != 200:
                print("⚠️ Request failed")
                return

            data = await response.json()
            
            if data.get("code") == "000000":
                # FIX: Access articles inside catalogs[0]
                catalogs = data.get("data", {}).get("catalogs", [])
                
                if not catalogs:
                    print("❌ No catalogs found")
                    return
                
                # Get articles from first catalog
                articles = catalogs[0].get("articles", [])
                
                print(f"📰 Found {len(articles)} recent Binance announcements:\n")

                for article in articles:
                    title = article.get("title", "")
                    release_date = article.get("releaseDate", "")
                    article_id = article.get("id", "")
                    code = article.get("code", "")
                    
                    # Convert timestamp to readable date
                    from datetime import datetime
                    date_readable = datetime.fromtimestamp(release_date / 1000).strftime('%Y-%m-%d %H:%M')

                    # Check for specific tokens
                    if "TURTLE" in title.upper():
                        print(f"🐢 FOUND TURTLE!")
                        print(f"   Title: {title}")
                        print(f"   Date: {date_readable}")
                        print(f"   URL: https://www.binance.com/en/support/announcement/detail/{code}")
                        print(f"   ✅ Your scanner SHOULD detect this\n")

                    elif "BLUAI" in title.upper() or "Bluwhale" in title:
                        print(f"🐋 FOUND BLUAI!")
                        print(f"   Title: {title}")
                        print(f"   Date: {date_readable}")
                        print(f"   URL: https://www.binance.com/en/support/announcement/detail/{code}")
                        print(f"   ✅ Your scanner SHOULD detect this\n")
                    
                    elif "Orochi" in title or "ON" in title:
                        print(f"🆕 FOUND NEW LISTING: Orochi (ON)")
                        print(f"   Title: {title}")
                        print(f"   Date: {date_readable}")
                        print(f"   URL: https://www.binance.com/en/support/announcement/detail/{code}")
                        print(f"   🚨 UPCOMING - Not listed yet!\n")

                    else:
                        # Show first 5 others
                        if articles.index(article) < 15:
                            print(f"   {date_readable} - {title[:60]}...")
            else:
                print(f"❌ API Error: {data.get('message')}")

asyncio.run(test_binance_api())
