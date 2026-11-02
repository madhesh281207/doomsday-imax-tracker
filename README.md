# Doomsday IMAX Booking Tracker

A free, GitHub Actions-based starter project that checks a configured cinema booking page for
**Avengers: Doomsday**, **Nexus Vijaya Mall IMAX, Chennai**, and the target date **17 December 2026**.
It sends a Telegram alert when it detects a likely bookable show.

> Important: cinema sites change their layouts and may block automated browsing. This project uses
> conservative page-text/link checks, not an official cinema API. A human should verify the booking
> page before buying. The first setup requires the exact booking/listing URL you want to monitor.
> Do not assume a movie listing means tickets are on sale.

## Included

- `tracker.py` — Playwright page checker and change detection
- `config.py` — target movie, theatre, date and detection terms
- `telegram.py` — Telegram message sender and manual test command
- `.github/workflows/check.yml` — scheduled GitHub Actions run every five minutes
- `requirements.txt` — Python dependencies
- `.env.example` — local configuration template

## 1. Create a Telegram bot (free)

1. Open Telegram and message **@BotFather**.
2. Send `/newbot` and follow its instructions.
3. Copy the bot token. Keep it private.
4. Open your new bot and press **Start**.
5. To find your chat ID, message your bot once, then open this URL in a browser
   (replace `YOUR_TOKEN`): `https://api.telegram.org/botYOUR_TOKEN/getUpdates`
6. Find `"chat":{"id":...}` in the response. That number is your chat ID.
7. Never publish the token or commit it to GitHub.

If `getUpdates` is empty, send another message to the bot and refresh.

## 2. Add GitHub Actions secrets

In your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret | Value |
|---|---|
| `BOOKING_URL` | Exact official cinema/booking listing URL to check |
| `TELEGRAM_BOT_TOKEN` | Token from BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

Optional secrets:

| Secret | Purpose |
|---|---|
| `TARGET_DATE` | Defaults to `2026-12-17` |
| `THEATRE_KEYWORDS` | Defaults to `Nexus Vijaya Mall,IMAX` |
| `MOVIE_KEYWORDS` | Defaults to `Avengers: Doomsday,Avengers Doomsday` |

`BOOKING_URL` is intentionally required. Use the exact page where the theatre's showtimes or booking buttons appear. Prefer the cinema's own booking page or a recognised ticketing provider. Do not use a search-results URL.

## 3. Upload the files

1. Create a GitHub repository named `doomsday-imax-tracker`.
2. Upload all files and folders from this ZIP into the repository root.
3. Go to **Settings → Secrets and variables → Actions** and add the secrets above.
4. Go to **Actions**, enable workflows if GitHub asks, then run **Doomsday IMAX booking check** using **Run workflow**. For the first test, set **Send a Telegram test message before checking bookings** to `true`. You should receive a Telegram setup-test message; it does not mean bookings are open.

The workflow is scheduled with `*/5 * * * *` (every five minutes). GitHub's scheduler is best-effort: runs can be delayed, and it is not a guaranteed real-time alarm. GitHub Actions usage is free within the account's included limits.

## 4. Run locally (optional)

Python 3.10+ is recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env`, fill in the values, then run:

```bash
python tracker.py
```

The script reads environment variables directly. For local runs, export them in your terminal or use a local environment loader of your choice. `.env` is ignored by Git.

## Detection behaviour and limitations

The checker looks for the configured movie title, target date, cinema identity and IMAX format. A booking action must be found in the same nearby show-card context as the movie, date and IMAX label. Regular-screen shows and other IMAX movies must not trigger an alert.

It tries to avoid treating a plain movie announcement as a booking. However, page structures vary. A site may render showtimes only after choosing a date/location, use inaccessible scripts, or block automated browsers. If the checker cannot confidently detect a bookable show, it reports **NOT CONFIRMED** rather than claiming bookings are open.

The initial run stores a baseline and does not send an opening alert unless it detects a likely bookable show. Subsequent runs alert only when the status changes to detected. You can re-arm alerts by deleting `tracker_state.json` from the repository (if you choose to commit state) or by using the workflow artifact/state behaviour described below.

### State persistence

GitHub-hosted runners are temporary. This workflow downloads and uploads `tracker_state.json` as an artifact-backed cache between runs. GitHub artifact retention/cache behaviour can vary; for reliable persistent state, enable the repository's Actions cache or commit a small state file using a dedicated bot token. This starter uses `actions/cache` as a lightweight best-effort store. If state is lost, you may receive a duplicate alert.

## Privacy and safety

- Never put bot tokens in source code.
- Do not bypass logins, CAPTCHAs, paywalls, rate limits, or access controls.
- Keep the check interval at five minutes as configured; if the site objects, increase it or stop monitoring.
- The project does not purchase tickets or reserve seats.
