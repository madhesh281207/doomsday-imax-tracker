"""Telegram Bot API notifier and manual test command."""
import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request


def send_telegram(message: str) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data.get("ok"):
            raise RuntimeError(f"Telegram API returned an error: {data}")
        print("Telegram notification sent successfully.")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Telegram HTTP error {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Could not send Telegram notification: {exc}") from exc


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a Telegram test notification.")
    parser.add_argument("--test", action="store_true", help="Send a test message.")
    args = parser.parse_args()
    if args.test:
        send_telegram(
            "Doomsday IMAX Tracker test notification\n\n"
            "Telegram is connected. This is only a setup test; it does not mean "
            "Avengers: Doomsday bookings are open."
        )
    else:
        parser.print_help()
