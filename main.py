import os
import time
import requests
from datetime import datetime

URL = "https://tasadmin.iitkgp.ac.in/api/v1/swimming-form/getReleasedFormList"

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

CHECK_INTERVAL = 300  # seconds


def send_telegram(message):
    if not BOT_TOKEN or not CHAT_ID:
        return

    try:
        requests.get(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            params={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=10
        )
    except Exception as e:
        print("Telegram Error:", e)


def get_pgrs_data():
    response = requests.post(URL, timeout=15)

    if response.status_code != 200:
        raise Exception(f"HTTP {response.status_code}")

    data = response.json()

    for item in data["list"]:
        if item["category"] == "PGRS and Family":
            return {
                "available_form": item["available_form"],
                "form_released": item["form_released"]
            }

    raise Exception("PGRS and Family category not found")


print("Monitor Started")

send_telegram("🏊 PGRS Swimming Monitor Started")

previous_available = None
previous_released = None

while True:

    try:

        pgrs = get_pgrs_data()

        available = pgrs["available_form"]
        released = pgrs["form_released"]

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"[{now}] "
            f"Available={available} "
            f"Released={released}"
        )

        with open("monitor.log", "a") as log:
            log.write(
                f"{now},"
                f"{available},"
                f"{released}\n"
            )

        if previous_available is None:
            previous_available = available
            previous_released = released

        else:

            if available > previous_available:

                message = (
                    "🚨 SWIMMING SLOT AVAILABLE\n\n"
                    f"PGRS and Family\n"
                    f"Available Forms: "
                    f"{previous_available} → {available}\n"
                    f"Released Forms: {released}"
                )

                print(message)
                send_telegram(message)

            if released > previous_released:

                message = (
                    "📢 NEW FORMS RELEASED\n\n"
                    f"PGRS and Family\n"
                    f"Released Forms: "
                    f"{previous_released} → {released}\n"
                    f"Available Forms: {available}"
                )

                print(message)
                send_telegram(message)

            previous_available = available
            previous_released = released

    except Exception as e:

        print("Error:", e)

        try:
            send_telegram(f"Monitor Error: {e}")
        except:
            pass

    time.sleep(CHECK_INTERVAL)