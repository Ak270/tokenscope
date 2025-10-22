"""
Test if system can detect TURTLE listing
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
                print("⚠️ Request failed, possibly blocked.")
                text = await response.text()
                print(text[:500])
                return

            data = await response.json()

            print(f"Json: {data}")
            if data.get("code") == "000000":
                articles = data.get("data", {}).get("catalogs", [])
                print(f"📰 Found {len(articles)} announcements:\n")

                for article in articles[:10]:
                    title = article.get("title", "")
                    release_date = article.get("releaseDate", "")

                    if "TURTLE" in title.upper():
                        print(f"🐢 FOUND TURTLE ANNOUNCEMENT!")
                        print(f"   Title: {title}")
                        print(f"   Date: {release_date}\n")

                    elif "BLUAI" in title.upper():
                        print(f"🐋 FOUND BLUAI ANNOUNCEMENT!")
                        print(f"   Title: {title}")
                        print(f"   Date: {release_date}\n")

                    else:
                        print(f"   {title[:60]}...")

asyncio.run(test_binance_api())
