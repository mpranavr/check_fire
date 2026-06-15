import os
import time
import random
import requests
from datetime import datetime

# =====================================================
# CONFIGURATION
# =====================================================

URL = "https://tasadmin.iitkgp.ac.in/api/v1/swimming-form/getReleasedFormList"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Base interval in minutes
INTERVAL_TIME_MIN = int(os.getenv("INTERVAL_TIME_MIN", "6"))

# Random delay added after each check (seconds)
RANDOM_OFFSET_MIN = 0
RANDOM_OFFSET_MAX = 180

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36"
    )
}

# =====================================================
# VALIDATION
# =====================================================

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

if not CHAT_ID:
    raise ValueError("CHAT_ID environment variable not set")

# =====================================================
# TELEGRAM
# =====================================================

def send_telegram(message):
    try:

        response = requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=15
        )

        print(
            f"Telegram Status: {response.status_code}"
        )

        if response.status_code != 200:
            print(response.text)

    except Exception as e:
        print(f"Telegram Error: {e}")

# =====================================================
# API
# =====================================================

def get_pgrs_data():

    response = requests.post(
        URL,
        headers=HEADERS,
        timeout=15
    )

    if response.status_code != 200:
        raise Exception(
            f"API returned HTTP {response.status_code}"
        )

    data = response.json()

    if not data.get("success", False):
        raise Exception(
            "API returned success=False"
        )

    for item in data["list"]:

        if item["category"] == "PGRS and Family":

            return {
                "available_form": item["available_form"],
                "form_released": item["form_released"]
            }

    raise Exception(
        "PGRS and Family category not found"
    )

# =====================================================
# STARTUP
# =====================================================

print("=" * 60)
print("PGRS Swimming Monitor Started")
print(
    f"Base Interval: "
    f"{INTERVAL_TIME_MIN} minute(s)"
)
print("=" * 60)

send_telegram(
    "🏊 PGRS Swimming Monitor Started"
)

previous_available = None
previous_released = None

# =====================================================
# MAIN LOOP
# =====================================================

while True:

    try:

        pgrs = get_pgrs_data()

        available = pgrs["available_form"]
        released = pgrs["form_released"]

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        print(
            f"[{now}] "
            f"Available={available} "
            f"Released={released}"
        )

        # Optional logging
        with open("monitor.log", "a") as log:
            log.write(
                f"{now},"
                f"{available},"
                f"{released}\n"
            )

        # First iteration
        if previous_available is None:

            previous_available = available
            previous_released = released

            print(
                f"Initial State -> "
                f"Available={available}, "
                f"Released={released}"
            )

        else:

            # New available slots
            if available > previous_available:

                message = (
                    "🚨 SWIMMING SLOT AVAILABLE\n\n"
                    "Category: PGRS and Family\n"
                    f"Available Forms: "
                    f"{previous_available} → {available}\n"
                    f"Released Forms: {released}\n"
                    f"Time: {now}"
                )

                print("\n" + "=" * 60)
                print(message)
                print("=" * 60)

                send_telegram(message)

            # Admin released more forms
            if released > previous_released:

                message = (
                    "📢 NEW FORMS RELEASED\n\n"
                    "Category: PGRS and Family\n"
                    f"Released Forms: "
                    f"{previous_released} → {released}\n"
                    f"Available Forms: {available}\n"
                    f"Time: {now}"
                )

                print("\n" + "=" * 60)
                print(message)
                print("=" * 60)

                send_telegram(message)

            previous_available = available
            previous_released = released

    except Exception as e:

        error_msg = (
            f"[{datetime.now()}] "
            f"Monitor Error: {e}"
        )

        print(error_msg)

        try:
            send_telegram(error_msg)
        except:
            pass

    # =================================================
    # RANDOMIZED DELAY
    # =================================================

    random_offset = random.randint(
        RANDOM_OFFSET_MIN,
        RANDOM_OFFSET_MAX
    )

    sleep_time = (
        INTERVAL_TIME_MIN * 60
        + random_offset
    )

    print(
        f"Sleeping for "
        f"{sleep_time} sec "
        f"(random +{random_offset}s)"
    )

    time.sleep(sleep_time)