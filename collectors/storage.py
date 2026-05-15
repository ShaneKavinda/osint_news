import json
import sqlite3
from pathlib import Path
from typing import Iterable


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "events.db"


def init_db(db_path: Path = DB_PATH) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            external_id TEXT PRIMARY KEY,
            source_type TEXT,
            source_name TEXT,
            source_url TEXT,
            title TEXT,
            text TEXT,
            url TEXT,
            published_at TEXT,
            collected_at TEXT,
            language TEXT,
            hashtags TEXT,
            engagement TEXT,
            traction_score REAL,
            raw TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def save_items(items: Iterable[dict], db_path: Path = DB_PATH) -> int:
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    inserted = 0

    for item in items:
        cur.execute(
            """
            INSERT OR IGNORE INTO items (
                external_id,
                source_type,
                source_name,
                source_url,
                title,
                text,
                url,
                published_at,
                collected_at,
                language,
                hashtags,
                engagement,
                traction_score,
                raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item["external_id"],
                item["source_type"],
                item["source_name"],
                item.get("source_url"),
                item["title"],
                item["text"],
                item["url"],
                item.get("published_at"),
                item.get("collected_at"),
                item.get("language"),
                json.dumps(item.get("hashtags", []), ensure_ascii=False),
                json.dumps(item.get("engagement", {}), ensure_ascii=False),
                item.get("traction_score"),
                json.dumps(item.get("raw", {}), ensure_ascii=False),
            ),
        )
        inserted += cur.rowcount

    conn.commit()
    conn.close()

    return inserted
