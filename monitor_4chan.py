import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone

CATALOG_URL = "https://a.4cdn.org/pol/catalog.json"
KEYWORD = os.getenv("KEYWORD", "happening")
THRESHOLD = int(os.getenv("THRESHOLD", "40"))

# Optional: whole-word matching (set WHOLE_WORD=1 in env to enable)
WHOLE_WORD = os.getenv("WHOLE_WORD", "0") == "1"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def fetch_catalog():
    req = urllib.request.Request(
        CATALOG_URL,
        headers={"User-Agent": "keyword-monitor/1.0 (+github actions)"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def count_keyword(catalog, keyword: str) -> int:
    # Count occurrences across thread subject (sub) + comment/snippet (com)
    text_parts = []
    for page in catalog:
        for thread in page.get("threads", []):
            sub = thread.get("sub", "")
            com = thread.get("com", "")
            text_parts.append(sub)
            text_parts.append(com)

    haystack = "\n".join(text_parts).lower()
    needle = keyword.lower()

    if WHOLE_WORD:
        pattern = r"\b" + re.escape(needle) + r"\b"
        return len(re.findall(pattern, haystack))
    else:
        return haystack.count(needle)

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()

def main():
    catalog = fetch_catalog()
    count = count_keyword(catalog, KEYWORD)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    if count >= THRESHOLD:
        send_telegram(
            f"ALERT: '{KEYWORD}' count is {count} (>= {THRESHOLD}) on /pol/ catalog.\n"
            f"Time: {now}\n"
            f"Source: {CATALOG_URL}"
        )
    else:
        # Keep Actions logs useful without spamming Telegram
        print(f"{now} OK: '{KEYWORD}' count={count}, threshold={THRESHOLD}")

if __name__ == "__main__":
    main()
