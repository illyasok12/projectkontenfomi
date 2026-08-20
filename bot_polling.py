"""
FOMI 2-Way Interactive Bot — Local Polling Runner
=================================================
Jalankan script ini di terminal untuk langsung menguji bot 2 arah secara live
tanpa perlu menunggu deploy ke web server!

Cara pakai:
python bot_polling.py
"""

import os
import sys
import time
import requests

# UTF-8 untuk terminal
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Import core handler dari api/index.py
from api.index import handle_user_message, TELEGRAM_BOT_TOKEN, GEMINI_API_KEY


def run_polling():
    print("=" * 60)
    print("🤖 FOMI 2-Way Interactive Bot (Local Polling Mode)")
    print("=" * 60)
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN belum diset!")
        return
    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY belum diset!")
        return

    print("✅ Bot Token & Gemini API Key terdeteksi.")
    print("📡 Menghapus webhook lama (jika ada) untuk mengaktifkan polling...")
    
    # Hapus webhook agar getUpdates bisa jalan
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook")
    
    print("🚀 Bot AKTIF! Silakan buka chat @peojectkonten_bot di Telegram dan kirim pesan.")
    print("   Tekan Ctrl + C di terminal ini untuk berhenti.\n")

    offset = 0
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
            resp = requests.get(url, timeout=35)
            
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        text = msg.get("text", "")
                        user_name = msg.get("from", {}).get("first_name", "Kak")
                        
                        print(f"📩 Pesan masuk dari {user_name} ({chat_id}): '{text}'")
                        handle_user_message(chat_id, text, user_name)
                        print(f"   ↳ ✅ Selesai diproses & dibalas.")
            else:
                time.sleep(2)
        except KeyboardInterrupt:
            print("\n🛑 Polling dihentikan oleh user.")
            break
        except Exception as e:
            print(f"⚠️ Error polling: {e}")
            time.sleep(3)


if __name__ == "__main__":
    run_polling()
