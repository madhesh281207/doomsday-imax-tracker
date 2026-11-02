"""Minimal Telegram Bot API notifier."""
import json
import os
import urllib.error
import urllib.parse
import urllib.request


def send_telegram(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        print("Telegram not configured; skipping notification.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode()
    request = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API returned an error: {data}")
        print("Telegram notification sent.")
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not send Telegram notification: {exc}") from exc
