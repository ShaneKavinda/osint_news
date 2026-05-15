import feedparser
import pandas as pd
from datetime import datetime, timezone
try:
    from collectors.storage import save_items
except ModuleNotFoundError:
    from storage import save_items

RSS_FEEDS = ["https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
             
             ]

class ErrorResponse(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


# Fetch news from the RSS feeds
def fetch_news(news_titles: list[dict], url: str):
    try:
        feed = feedparser.parse(url)
        status = feed.get("status")

        if status and status != 200:
            raise ErrorResponse(status_code=status)

        if not feed.entries:
            error = getattr(feed, "bozo_exception", "No entries returned")
            print(f"No RSS entries returned for {url}: {error}")
            return

        for entry in feed.entries:
            news_titles.append(normalize_rss_entry(url, feed, entry))
    except ErrorResponse as e:
        print("Error response:", e.status_code)


def normalize_rss_entry(feed_url: str, feed, entry) -> dict:
    source_name = feed.feed.get("title", feed_url)
    source_url = feed.feed.get("link", feed_url)
    article_url = entry.get("link")
    guid = entry.get("id") or article_url
    summary = entry.get("description") or entry.get("summary") or ""
    published_at = None

    if entry.get("published_parsed"):
        published_at = datetime(
            *entry.published_parsed[:6],
            tzinfo=timezone.utc,
        ).isoformat()
    elif entry.get("updated_parsed"):
        published_at = datetime(
            *entry.updated_parsed[:6],
            tzinfo=timezone.utc,
        ).isoformat()

    return {
        "source_type": "rss",
        "source_name": source_name,
        "source_url": source_url,
        "external_id": f"rss:{source_name}:{guid}",
        "title": entry.get("title", "").strip(),
        "text": summary.strip(),
        "url": article_url,
        "published_at": published_at,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "language": feed.feed.get("language"),
        "hashtags": [],
        "engagement": {},
        "traction_score": None,
        "raw": {
            "feed_url": feed_url,
            "guid": guid,
            "published": entry.get("published"),
        },
    }

# Save the fetched news titles in a csv file
def save_to_csv(df):
    print("saving to file.....")
    df.to_csv("news_titles.csv", index=False, )
    print("saved to file!")

# Convert the news titles to a Pandas Dataframe
def to_dataframe(news_titles_arr):
    print("creating a pandas dataframe from fetched news articles...")
    df = pd.DataFrame(news_titles_arr)
    print("news dataframe created")
    return df

def main():
    news_titles = []
    for url in RSS_FEEDS:
        fetch_news(news_titles, url)
    inserted = save_items(news_titles)
    news_df = to_dataframe(news_titles)
    save_to_csv(news_df)
    print(f"Saved {inserted} new normalized RSS rows to data/events.db")

if __name__ == "__main__":
    main()
