import json
import os
from pathlib import Path

import feedparser
import requests


RSS_FEEDS = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
    "https://www.artificialintelligence-news.com/feed/",
]

STATE_FILE = Path("published.json")
MAX_POSTS_PER_RUN = 3


def load_published():
    if not STATE_FILE.exists():
        return set()

    try:
        return set(json.loads(STATE_FILE.read_text(encoding="utf-8")))
    except Exception:
        return set()


def save_published(published):
    STATE_FILE.write_text(
        json.dumps(list(published)[-300:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def make_post(entry):
    title = entry.get("title", "Новая новость")
    summary = entry.get("summary", "").strip()
    link = entry.get("link", "")

    summary = summary.replace("<p>", "").replace("</p>", "")
    summary = summary[:600]

    return f"🤖 {title}\n\n{summary}\n\nИсточник: {link}"


def send_to_telegram(text):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    channel = os.environ["TELEGRAM_CHANNEL"]

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": channel,
            "text": text,
            "disable_web_page_preview": False,
        },
        timeout=30,
    )

    response.raise_for_status()


def main():
    published = load_published()
    new_entries = []

    for feed_url in RSS_FEEDS:
        feed = feedparser.parse(feed_url)

        for entry in feed.entries:
            link = entry.get("link")

            if link and link not in published:
                new_entries.append(entry)

    new_entries = new_entries[:MAX_POSTS_PER_RUN]

    for entry in reversed(new_entries):
        send_to_telegram(make_post(entry))
        published.add(entry["link"])

    save_published(published)
    print(f"Опубликовано новостей: {len(new_entries)}")


if __name__ == "__main__":
    main()
