import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime, timezone


COOLDOWN_SECONDS = 60 * 60  # 60 minutes
LAST_ALARM_FILE = ".last_alarm"
CATALOG_URL = "https://a.4cdn.org/pol/catalog.json"
KEYWORD = os.getenv("KEYWORD", "happening")
THRESHOLD = int(os.getenv("THRESHOLD", "25"))

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

def send_pushover_emergency(message: str):
    data = urllib.parse.urlencode({
        "token": os.environ["PUSHOVER_APP_TOKEN"],
        "user": os.environ["PUSHOVER_USER_KEY"],
        "message": message,
        "priority": 2,          # EMERGENCY
        "retry": 30,             # repeat every 30s
        "expire": 3600,          # for up to 1 hour
        "sound": "echo"         # loud alarm sound
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.pushover.net/1/messages.json",
        data=data,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=20) as resp:
        resp.read()

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

def get_last_alarm_time():
    if not os.path.exists(LAST_ALARM_FILE):
        return None
    try:
        with open(LAST_ALARM_FILE, "r") as f:
            return float(f.read().strip())
    except Exception:
        return None

def set_last_alarm_time(ts: float):
    with open(LAST_ALARM_FILE, "w") as f:
        f.write(str(ts))

def main():
    catalog = fetch_catalog()
    count = count_keyword(catalog, KEYWORD)

    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d %H:%M UTC")
    now_ts = now_dt.timestamp()

    if count >= THRESHOLD:
        last_alarm = get_last_alarm_time()

        if last_alarm and (now_ts - last_alarm) < COOLDOWN_SECONDS:
            remaining = int((COOLDOWN_SECONDS - (now_ts - last_alarm)) / 60)
            print(
                f"{now_str} ABOVE threshold, "
                f"but cooldown active ({remaining} min remaining)"
            )
            return

        # 🔔 FIRE ALARM
        send_pushover_emergency(
            f"🚨 KEYWORD ALARM 🚨\n"
            f"'{KEYWORD}' count is {count} (>= {THRESHOLD}) on /pol/ catalog.\n"
            f"Time: {now_str}\n"
            f"Check /pol/ catalog immediately."
        )

        send_telegram(
            f"ALERT: '{KEYWORD}' count is {count} (>= {THRESHOLD}) on /pol/ catalog.\n"
            f"Time: {now_str}\n"
            f"Source: {CATALOG_URL}"
        )

        set_last_alarm_time(now_ts)

    else:
        print(f"{now_str} OK: '{KEYWORD}' count={count}, threshold={THRESHOLD}")

if __name__ == "__main__":
    main()
