import requests
from bs4 import BeautifulSoup
import pandas as pd
import datetime
import time
# We assume twikit is installed and handles Twitter interaction
try:
    from twikit.twitter import TwitterClient
except ImportError:
    print("Error: 'twikit' library not found. Please ensure it is installed.")
    TwitterClient = None

COLLECTOR_DIR = "collectors"

def get_trending_hashtags(source_url: str) -> list[str]:
    """
    Scrapes trending hashtags from a given public source URL (e.g., trends24).
    This function is highly dependent on the website's structure and may need updates.
    """
    print(f"Attempting to scrape trends from: {source_url}")
    try:
        # Fetch the page content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/Chrome'
        }
        response = requests.get(source_url, headers=headers, timeout=10)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Placeholder logic: You need to find the correct CSS selector/HTML tag for trends on the target site.
        # Example assumption based on common web structures:
        trend_elements = soup.find_all('a', class_='hashtag-link') # <--- !!! UPDATE THIS CLASS NAME !!!
        
        hashtags = []
        for element in trend_elements[:10]: # Limit to 10 for safety
            # Extract the hashtag text, e.g., "#TopicName"
            text = element.get_text(strip=True)
            if text and text.startswith('#'):
                hashtags.append(text[1:]) # Remove '#' for cleaner data
        
        print(f"Scraped {len(hashtags)} potential hashtags.")
        return list(set(hashtags))

    except requests.exceptions.RequestException as e:
        print(f"Error scraping trends from {source_url}: {e}")
        # Fallback to a predefined list if scraping fails
        return ["trendingtopic1", "technews", "worldevents"]


def fetch_top_tweets(hashtags: list[str]) -> pd.DataFrame:
    """
    Uses twikit/TwitterClient to fetch the top tweets for a list of hashtags.
    Returns a DataFrame containing structured tweet data.
    """
    if not TwitterClient:
        print("Cannot fetch tweets because twikit is not available or initialized.")
        return pd.DataFrame()

    all_tweet_data = []
    # In a real scenario, API keys and authentication would be loaded from environment variables
    # Example Client Initialization (Requires actual credentials setup)
    try:
        print("Attempting to initialize Twitter client...")
        client = TwitterClient(api_key="YOUR_API_KEY", api_secret="YOUR_SECRET")
        client.connect() # Assuming connect() method exists
        print("Twitter Client connected successfully.")
    except Exception as e:
        print(f"Error initializing Twitter Client (check credentials/setup): {e}")
        return pd.DataFrame()

    for hashtag in hashtags:
        print(f"\nFetching tweets for: #{hashtag}...")
        try:
            # Assuming the client has a method to fetch tweets by hashtag
            tweets = client.get_tweets_by_hashtag(query=hashtag, limit=5) 
            
            for tweet in tweets:
                all_tweet_data.append({
                    'Hashtag': f"#{hashtag}",
                    'Tweet Text': tweet['text'],
                    'User ID': str(tweet['user']['id']),
                    'Author Username': tweet['user']['screen_name'],
                    'Post Date/Time': tweet['created_at'],
                })
            print(f"Successfully collected {len(tweets)} tweets for #{hashtag}.")

        except Exception as e:
            print(f"Could not fetch tweets for #{hashtag}. Error: {e}")

    return pd.DataFrame(all_tweet_data)


def run_collector():
    """Main function to orchestrate the data collection process."""
    print("--- Starting Twitter Data Collector ---")
    
    # Step 1: Fetch Trending Hashtags (using a public scrape URL as per plan/user choice)
    TWEETR_SOURCE_URL = "https://trends24.in" # Example placeholder URL
    hashtags = get_trending_hashtags(TWEETR_SOURCE_URL)

    if not hashtags:
        print("Could not retrieve any trending hashtags. Exiting.")
        return pd.DataFrame()
    
    # Step 2: Fetch Top Tweets for each hashtag
    tweet_df = fetch_top_tweets(hashtags)

    # Step 3: Save to Parquet
    if not tweet_df.empty:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"twitter_trends_{timestamp_str}.parquet"
        output_filepath = f"{COLLECTOR_DIR}/{output_filename}"
        
        try:
            # Ensure the directory exists
            import os
            os.makedirs(COLLECTOR_DIR, exist_ok=True)
            
            tweet_df.to_parquet(output_filepath, index=False)
            print(f"\n✅ Success! All data saved to {output_filepath}")
        except Exception as e:
            print(f"Error saving Parquet file: {e}")

    return tweet_df

if __name__ == "__main__":
    # Note: This script is a template. Actual API keys and scraper selectors 
    # must be implemented by the user based on the target site/API documentation.
    run_collector()