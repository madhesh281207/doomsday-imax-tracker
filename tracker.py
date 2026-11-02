"""Check a configured booking page for a likely bookable Doomsday IMAX show."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

from config import (
    BOOKING_TERMS, FORMAT_KEYWORDS, HEADLESS, MOVIE_KEYWORDS, NON_BOOKING_TERMS,
    PAGE_TIMEOUT_MS, TARGET_DATE, THEATRE_KEYWORDS,
)
from telegram import send_telegram

STATE_FILE = Path("tracker_state.json")


def date_variants(iso_date: str) -> list[str]:
    dt = datetime.strptime(iso_date, "%Y-%m-%d")
    return [
        dt.strftime("%d %B %Y").lower(),       # 17 December 2026
        dt.strftime("%d %b %Y").lower(),       # 17 Dec 2026
        dt.strftime("%d-%m-%Y"),               # 17-12-2026
        dt.strftime("%d/%m/%Y"),               # 17/12/2026
        dt.strftime("%Y-%m-%d"),               # 2026-12-17
        dt.strftime("%d %B").lower(),          # 17 December
        dt.strftime("%d %b").lower(),          # 17 Dec
    ]


def contains_any(text: str, terms: list[str] | tuple[str, ...]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"status": "unknown", "last_url": "", "last_checked": ""}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def inspect_page(page, booking_url: str) -> tuple[bool, str]:
    page.goto(booking_url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except PlaywrightTimeoutError:
        # Some ticketing sites keep analytics/polling connections open.
        pass
    page.wait_for_timeout(2500)

    title = page.title()
    body = page.locator("body").inner_text(timeout=10000)
    page_text = f"{title}\n{body}"
    lower = page_text.lower()

    movie_found = contains_any(lower, MOVIE_KEYWORDS)
    date_found = contains_any(lower, date_variants(TARGET_DATE))
    theatre_found = contains_any(lower, THEATRE_KEYWORDS)
    imax_found = contains_any(lower, FORMAT_KEYWORDS)

    # Look for actionable booking links/buttons, retaining their nearby text
    # so a generic "Book" button elsewhere does not automatically count.
    actions = page.locator("a, button, [role='button'], input[type='submit']")
    action_evidence = []
    for i in range(min(actions.count(), 500)):
        item = actions.nth(i)
        try:
            label = (item.inner_text(timeout=500) or item.get_attribute("aria-label") or
                     item.get_attribute("value") or "").strip()
            href = item.get_attribute("href") or ""
            disabled = item.is_disabled() if item.evaluate(
                "(el) => el.tagName === 'BUTTON' || el.getAttribute('role') === 'button'"
            ) else False
            if disabled:
                continue
            if contains_any(label, BOOKING_TERMS) or (
                "book" in href.lower() and href.strip() not in ("", "#")
            ):
                context = item.evaluate(
                    "(el) => (el.closest('article, li, section, [class*=\"show\"], "
                    "[class*=\"event\"], [class*=\"movie\"], [class*=\"card\"] ) "
                    "|| el.parentElement || el).innerText"
                )
                context = (context or label).lower()
                action_evidence.append({
                    "label": label[:120],
                    "href": href,
                    "context": context[:1500],
                })
        except Exception:
            continue

    # A candidate action must belong to a show card that contains the
    # requested movie, target date AND IMAX. This avoids matching a different
    # IMAX film or a regular-screen Doomsday listing elsewhere on the page.
    confirmed_actions = [
        item for item in action_evidence
        if contains_any(item["context"], MOVIE_KEYWORDS)
        and contains_any(item["context"], date_variants(TARGET_DATE))
        and contains_any(item["context"], FORMAT_KEYWORDS)
        and not contains_any(item["context"], NON_BOOKING_TERMS)
    ]
    confirmed_action = bool(confirmed_actions)
    detected = (
        movie_found and date_found and theatre_found and imax_found
        and confirmed_action
    )

    diagnostics = (
        f"Page title: {title!r}\n"
        f"Movie keyword found: {movie_found}\n"
        f"Target date found: {date_found}\n"
        f"Theatre/format keywords found: {theatre_found}\n"
        f"Enabled booking action found in relevant context: {confirmed_action}\n"
        f"Candidate booking actions: {len(action_evidence)}\n"
        f"URL: {page.url}\n"
    )
    return detected, diagnostics


def main() -> int:
    booking_url = os.getenv("BOOKING_URL", "").strip()
    if not booking_url:
        raise SystemExit("Missing BOOKING_URL environment variable.")
    parsed = urlparse(booking_url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise SystemExit("BOOKING_URL must be a valid http(s) URL.")

    now = datetime.now(timezone.utc).isoformat()
    state = load_state()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=HEADLESS)
            page = browser.new_page(
                user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 Chrome/124 Safari/537.36")
            )
            page.set_default_timeout(10000)
            detected, diagnostics = inspect_page(page, booking_url)
            final_url = page.url
            browser.close()
    except Exception as exc:
        print(f"Check failed: {type(exc).__name__}: {exc}")
        return 2

    previous = state.get("status", "unknown")
    current = "bookings_detected" if detected else "not_confirmed"
    print(f"Checked at {now}\n{diagnostics}")
    print(f"Previous status: {previous}; current status: {current}")

    if detected and previous != "bookings_detected":
        message = (
            "🎟️ POSSIBLE DOOMSDAY IMAX BOOKING OPENING!\n\n"
            "Movie: Avengers: Doomsday\n"
            "Theatre: Nexus Vijaya Mall IMAX, Chennai\n"
            f"Target date: {TARGET_DATE}\n\n"
            "The tracker detected an enabled booking action. Open the page and "
            "verify the show and seats before purchasing:\n"
            f"{final_url}\n\n"
            "This is an automated detection, not a guaranteed confirmation."
        )
        send_telegram(message)
    elif not detected:
        print("No matching bookable IMAX show detected. No alert sent.")

    state.update({
        "status": current,
        "last_url": final_url,
        "last_checked": now,
    })
    save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
