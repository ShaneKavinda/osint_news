import os
import re
import json
import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

try:
    from collectors.storage import save_items
except ModuleNotFoundError:
    from storage import save_items

load_dotenv(Path(__file__).with_name(".env"))

api_id_raw = os.getenv("TELEGRAM_API_ID")
API_ID = int(api_id_raw) if api_id_raw else None
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION_NAME = os.getenv("TELEGRAM_SESSION_NAME", "telegram_session")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

STATE_FILE = DATA_DIR / "telegram_state.json"

IMPORTANT_KEYWORDS = [
    "breaking",
    "explosion",
    "fire",
    "missile",
    "attack",
    "evacuation",
    "earthquake",
    "outage",
    "cyberattack",
    "breach",
    "contamination",
    "recall",
]


def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(
        json.dumps(state, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def extract_hashtags(text: str) -> list[str]:
    if not text:
        return []
    return sorted(set(re.findall(r"#(\w+)", text)))


def hours_since(iso_time: str | None) -> float:
    if not iso_time:
        return 0.01

    published = datetime.fromisoformat(iso_time)
    now = datetime.now(timezone.utc)

    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    return max((now - published).total_seconds() / 3600, 0.01)


def telegram_traction_score(item: dict) -> float:
    engagement = item.get("engagement", {})

    views = engagement.get("views") or 0
    forwards = engagement.get("forwards") or 0
    replies = engagement.get("replies") or 0
    age_hours = hours_since(item.get("published_at"))

    weighted_engagement = views + 10 * forwards + 5 * replies
    return weighted_engagement / age_hours


def is_alert_candidate(item: dict, score_threshold: float = 500) -> bool:
    text = f"{item.get('title', '')} {item.get('text', '')}".lower()
    keyword_hit = any(keyword in text for keyword in IMPORTANT_KEYWORDS)
    return keyword_hit and telegram_traction_score(item) > score_threshold


def format_alert(item: dict) -> str:
    score = telegram_traction_score(item)
    engagement = item.get("engagement", {})

    return f"""
Emerging Telegram Signal

Source: {item["source_name"]}
Title: {item["title"]}
Published: {item["published_at"]}
URL: {item["url"]}

Views: {engagement.get("views")}
Forwards: {engagement.get("forwards")}
Replies: {engagement.get("replies")}
Traction score: {score:.2f}

Status: Unverified social media signal.
Action: Cross-check with RSS, GDELT, official sources, and other social sources.
""".strip()


def normalize_telegram_message(channel_username: str, message) -> dict | None:
    text = message.message or ""

    # Skip empty service messages
    if not text.strip():
        return None

    channel_clean = channel_username.replace("@", "")
    message_url = f"https://t.me/{channel_clean}/{message.id}"

    title = text.strip().split("\n")[0][:180]

    item = {
        "source_type": "telegram",
        "source_name": channel_clean,
        "source_url": f"https://t.me/{channel_clean}",
        "external_id": f"telegram:{channel_clean}:{message.id}",
        "title": title,
        "text": text.strip(),
        "url": message_url,
        "published_at": message.date.astimezone(timezone.utc).isoformat()
        if message.date else None,
        "collected_at": datetime.now(timezone.utc).isoformat(),
        "language": None,
        "hashtags": extract_hashtags(text),
        "engagement": {
            "views": getattr(message, "views", None),
            "forwards": getattr(message, "forwards", None),
            "replies": (
                getattr(message.replies, "replies", None)
                if getattr(message, "replies", None)
                else None
            ),
        },
        "raw": {
            "telegram_message_id": message.id,
            "grouped_id": str(message.grouped_id) if message.grouped_id else None,
            "has_media": bool(message.media),
        },
    }

    item["traction_score"] = telegram_traction_score(item)
    item["raw"]["is_alert_candidate"] = is_alert_candidate(item)

    return item


async def fetch_channel_messages(
    channel_username: str,
    limit: int = 50,
    only_new: bool = True
) -> list[dict]:
    state = load_state()
    channel_key = channel_username.replace("@", "")
    last_seen_id = state.get(channel_key, {}).get("last_seen_id", 0)

    items = []

    if not API_ID or not API_HASH:
        raise RuntimeError(
            "Missing TELEGRAM_API_ID or TELEGRAM_API_HASH in collectors/.env"
        )

    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

    try:
        await client.connect()

        if not await client.is_user_authorized():
            if not sys.stdin.isatty():
                raise RuntimeError(
                    "Telegram login is required. Run this collector in an "
                    "interactive terminal once so Telethon can ask for your "
                    f"phone/code and create the {SESSION_NAME}.session file."
                )
            await client.start()

        entity = await client.get_entity(channel_username)

        async for message in client.iter_messages(entity, limit=limit):
            if only_new and message.id <= last_seen_id:
                continue

            item = normalize_telegram_message(channel_username, message)
            if item:
                items.append(item)
    except EOFError as exc:
        raise RuntimeError(
            "Telegram login is required. Run this collector in an interactive "
            "terminal once so Telethon can ask for your phone/code and create "
            f"the {SESSION_NAME}.session file."
        ) from exc
    finally:
        await client.disconnect()

    if items:
        newest_id = max(int(item["raw"]["telegram_message_id"]) for item in items)
        state[channel_key] = {
            "last_seen_id": max(last_seen_id, newest_id),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        save_state(state)

    # Return oldest first so downstream logic processes in chronological order
    return sorted(items, key=lambda x: x["published_at"] or "")


async def main():
    channel = "@OSINTdefender"
    items = await fetch_channel_messages(channel, limit=30, only_new=True)
    inserted = save_items(items)

    output_file = DATA_DIR / "telegram_osintdefender_latest.jsonl"

    with output_file.open("a", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    top_signals = sorted(
        items,
        key=lambda item: item.get("traction_score") or 0,
        reverse=True,
    )[:5]

    print(f"Collected {len(items)} new Telegram messages from {channel}")
    print(f"Saved {inserted} new rows to data/events.db")

    if top_signals:
        print("\nTop Telegram signals by traction score:")
        for rank, item in enumerate(top_signals, start=1):
            print(
                f"{rank}. {item['traction_score']:.2f} | "
                f"{item['source_name']} | {item['title']} | {item['url']}"
            )

    alerts = [item for item in items if is_alert_candidate(item)]
    if alerts:
        print("\nAlert candidates:")
        for alert in alerts:
            print()
            print(format_alert(alert))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as exc:
        print(f"Error: {exc}")
        sys.exit(1)
