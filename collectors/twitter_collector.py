import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
import os
import re
from urllib.parse import quote_plus
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

COLLECTOR_DIR = "collectors"
MAX_HASHTAGS = 10
REQUEST_DELAY_SECONDS = random.randint(3, 10)


def get_trending_hashtags(source_url: str) -> list[str]:
    print(f"Attempting to scrape trends from: {source_url}")

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/91.0.4472.124 Safari/537.36"
            )
        }

        response = requests.get(source_url, headers=headers, timeout=10)
        response.raise_for_status()

    except requests.exceptions.RequestException as e:
        print(f"Error accessing trend page {source_url}: {e}")
        print("Falling back to hardcoded trends.")
        return ["trendingtopic1", "technews", "worldevents"]

    soup = BeautifulSoup(response.content, "html.parser")
    hashtags = set()

    trend_links = soup.find_all("a", class_="trend-link")

    for link in trend_links:
        href = link.get("href", "")
        text = link.get_text(strip=True)

        raw_hashtag = None

        if text:
            raw_hashtag = text.lstrip("#").strip()
        elif href:
            match = re.search(r"(?:[?&]q=|/#)([a-zA-Z0-9_]+)", href)
            if match:
                raw_hashtag = match.group(1)

        if raw_hashtag:
            decoded = requests.utils.unquote(raw_hashtag).lstrip("#").strip()
            if len(decoded) > 2:
                hashtags.add(decoded)

    final_list = sorted(list(hashtags))
    print(f"Scraped {len(final_list)} unique hashtags/topics from the page.")
    return final_list


def fetch_nitter_html_with_playwright(page, query: str) -> str:
    url = f"https://nitter.net/search?f=tweets&q={quote_plus(query)}"
    print(f"Opening with browser: {url}")

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)

        # Give Nitter a little time to render/load timeline content.
        page.wait_for_timeout(3000)

        html = page.content()

        print("HTML length from browser:", len(html))
        print("First 300 chars:", repr(html[:300]))

        return html

    except PlaywrightTimeoutError:
        print(f"Playwright timeout for query: {query}")
        return ""
    except Exception as e:
        print(f"Playwright error for query {query}: {e}")
        return ""


def parse_nitter_tweets_from_html(html: str, query: str, max_tweets: int = 5) -> list[dict]:
    if not html.strip():
        return []

    soup = BeautifulSoup(html, "html.parser")

    tweet_containers = soup.select(".timeline-item")

    if not tweet_containers:
        print(f"No .timeline-item containers found for {query}.")
        return []

    rows = []

    for container in tweet_containers[:max_tweets]:
        text_el = container.select_one(".tweet-content")
        user_el = container.select_one(".username")
        fullname_el = container.select_one(".fullname")
        date_el = container.select_one(".tweet-date a")
        avatar_el = container.select_one(".avatar")
        media_el = container.select_one(".attachments, .gallery-row, .attachment")

        tweet_text = text_el.get_text(" ", strip=True) if text_el else ""
        username = user_el.get_text(strip=True) if user_el else "Unknown"
        fullname = fullname_el.get_text(" ", strip=True) if fullname_el else ""
        post_time = date_el.get("title") if date_el else ""
        relative_link = date_el.get("href") if date_el else ""

        if relative_link.startswith("/"):
            tweet_url = "https://nitter.net" + relative_link
        else:
            tweet_url = relative_link

        has_media = "Yes" if media_el else "No"

        if tweet_text:
            rows.append({
                "Trend": query,
                "Hashtag": f"#{query}",
                "Author Name": fullname,
                "Author Username": username,
                "Tweet Text": tweet_text,
                "Post Date/Time": post_time,
                "Tweet URL": tweet_url,
                "Has Media": has_media,
                "Source": "Nitter HTML via Playwright",
                "Collection Time": datetime.datetime.now().isoformat(timespec="seconds"),
            })

    return rows


def fetch_top_tweets_with_playwright(hashtags: list[str]) -> pd.DataFrame:
    all_rows = []

    print("--- Starting Tweet Collection from Nitter using Playwright ---")

    if MAX_HASHTAGS is not None:
        hashtags = hashtags[:MAX_HASHTAGS]

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:150.0) "
                "Gecko/20100101 Firefox/150.0"
            ),
            viewport={"width": 1366, "height": 768},
            locale="en-US",
        )

        page = context.new_page()

        for hashtag in hashtags:
            print(f"\nCollecting tweets for: {hashtag}")

            html = fetch_nitter_html_with_playwright(page, hashtag)
            rows = parse_nitter_tweets_from_html(html, hashtag, max_tweets=5)

            if rows:
                print(f"Collected {len(rows)} tweets for {hashtag}.")
                all_rows.extend(rows)
            else:
                print(f"No tweets collected for {hashtag}.")

            time.sleep(REQUEST_DELAY_SECONDS)

        browser.close()

    return pd.DataFrame(all_rows)


def run_collector():
    print("--- Starting Twitter/Nitter Browser Collector ---")

    trends_source_url = "https://trends24.in"
    hashtags = get_trending_hashtags(trends_source_url)

    if not hashtags:
        print("Could not retrieve any trending hashtags/topics. Exiting.")
        return pd.DataFrame()

    tweet_df = fetch_top_tweets_with_playwright(hashtags)

    if tweet_df.empty:
        print("\nNo tweet data collected.")
        return tweet_df

    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"twitter_trends_nitter_browser_{timestamp_str}.parquet"
    output_filepath = os.path.join("data", output_filename)

    try:
        os.makedirs(COLLECTOR_DIR, exist_ok=True)
        tweet_df.to_parquet(output_filepath, index=False)
        print(f"\n✅ Success! Data saved to {output_filepath}")
    except Exception as e:
        print(f"Error saving Parquet file: {e}")

    print("\nPreview:")
    print(tweet_df.head())

    return tweet_df


if __name__ == "__main__":
    run_collector()