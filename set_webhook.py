"""
Set or Delete Telegram Webhook
==============================
Gunakan script ini untuk menghubungkan bot Telegram ke URL Vercel kamu.

Cara pakai:
python set_webhook.py https://projectkontenfomi.vercel.app
"""

import sys
import os
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8663086142:AAGnuPV75KbmilWgQ8d81S3N4Vrf85bahgA")


def main():
    if len(sys.argv) < 2:
        print("Penggunaan:")
        print("  Set Webhook:    python set_webhook.py https://your-vercel-domain.vercel.app")
        print("  Delete Webhook: python set_webhook.py delete")
        return

    arg = sys.argv[1].strip()

    if arg.lower() == "delete":
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook"
        r = requests.get(url).json()
        print(f"🗑️ Delete webhook result: {r}")
    else:
        webhook_url = arg.rstrip("/") + "/"
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"
        r = requests.get(url).json()
        print(f"🔗 Set webhook result to {webhook_url}: {r}")

        # Check status
        info = requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getWebhookInfo").json()
        print(f"ℹ️ Current webhook info: {info}")


if __name__ == "__main__":
    main()
