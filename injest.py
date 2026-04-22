import feedparser
import pandas as pd
from typing import List

RSS_FEEDS = ["https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
             
             ]

class ErrorResponse(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


# Fetch news from the RSS feeds
def fetch_news(news_titles: List[str], url: str):
    try:
        feed = feedparser.parse(url)
        if feed.status == 200:
            for entry in feed.entries:
                print(f"Title: {entry.title}, URL: {entry.link}")
                news_titles.append(entry.title)
        else:
            raise ErrorResponse(status_code=feed.status)
    except ErrorResponse as e:
        print("Error response:", e.status_code)

# Save the fetched news titles in a csv file
def save_to_csv(df):
    print("saving to file.....")
    df.to_csv("news_titles.csv", index=False, )
    print("saved to file!")

# Convert the news titles to a Pandas Dataframe
def to_dataframe(news_titles_arr):
    print("creating a pandas dataframe from fetched news articles")
    df = pd.DataFrame(news_titles_arr)
    print("news dataframe created")
    return df

def main():
    news_titles = []
    for url in RSS_FEEDS:
        fetch_news(news_titles, url)
    news_df = to_dataframe(news_titles)
    save_to_csv(news_df)

if __name__ == "__main__":
    main()