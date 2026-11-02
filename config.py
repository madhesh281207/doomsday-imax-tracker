"""Target configuration for the Doomsday IMAX tracker."""
import os

MOVIE_KEYWORDS = [
    item.strip() for item in os.getenv(
        "MOVIE_KEYWORDS", "Avengers: Doomsday,Avengers Doomsday"
    ).split(",") if item.strip()
]
THEATRE_KEYWORDS = [
    item.strip() for item in os.getenv(
        "THEATRE_KEYWORDS", "Nexus Vijaya Mall,IMAX"
    ).split(",") if item.strip()
]
TARGET_DATE = os.getenv("TARGET_DATE", "2026-12-17")

# Booking language. Detection requires a movie + date + theatre/format context
# and a booking action/link in the same page area (or a booking URL).
BOOKING_TERMS = (
    "book", "book tickets", "buy tickets", "select seats",
    "proceed to pay", "available seats", "choose seats",
)
NON_BOOKING_TERMS = (
    "coming soon", "notify me", "remind me", "trailer",
    "teaser", "learn more", "more details",
)

PAGE_TIMEOUT_MS = int(os.getenv("PAGE_TIMEOUT_MS", "45000"))
HEADLESS = os.getenv("HEADLESS", "true").lower() != "false"
