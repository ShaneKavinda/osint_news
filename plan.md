1. Research about nitter and integrate it to our ingest.py to get latest twitter trends
2. save the output to a format that can load fast and allows processing


## Telegram integration

````bash
RSS feeds          Telegram channels
   ↓                     ↓
RSS collector       Telegram collector
   ↓                     ↓
    normalized_event_items
                ↓
            database
                ↓
    trend / anomaly / alert logic
````

### Use the same structure to store results from RSS feed and Telegram

example:

````bash
{
    "source_type": "telegram",
    "source_name": "OSINTdefender",
    "source_url": "https://t.me/OSINTdefender",
    "external_id": "telegram:OSINTdefender:12345",
    "title": "...",
    "text": "...",
    "url": "https://t.me/OSINTdefender/12345",
    "published_at": "2026-05-13T10:30:00+00:00",
    "collected_at": "2026-05-13T10:35:00+00:00",
    "language": "en",
    "hashtags": ["Iran", "USA"],
    "engagement": {
        "views": 1234,
        "forwards": 12,
        "replies": None
    },
    "raw": {}
}

{
    "source_type": "rss",
    "source_name": "BBC",
    "source_url": "...",
    "external_id": "rss:bbc:article-url-or-guid",
    "title": "...",
    "text": "...",
    "url": "...",
    "published_at": "...",
    "collected_at": "...",
    "language": "en",
    "hashtags": [],
    "engagement": {},
    "raw": {}
}
````

raw telegram messages -> clean + normalize -> extract entities/keywords -> cluster similar messages -> score urgency + traction -> cross check against RSS/GDELT/official sources


