# 🫧 FOMI Daily Content Engine

Sistem otomatis yang berjalan **setiap hari jam 7 pagi WIB** tanpa laptop harus menyala.

## Alur Kerja

```
Jam 07:00 WIB (GitHub Actions trigger)
        │
        ▼
[1] Scrape trending TikTok (via Apify)
        │
        ▼
[2] Scrape trending IG Reels (via Apify)
        │
        ▼
[3] Generate konsep konten FOMI (via Gemini AI)
        │
        ▼
[4] Kirim ke Telegram kamu 📱
```

## Setup

### 1. Push repo ini ke GitHub

```bash
git init
git add .
git commit -m "initial: fomi daily content engine"
git remote add origin https://github.com/USERNAME/fomi-daily-content.git
git push -u origin main
```

### 2. Tambahkan Secrets di GitHub

Buka: `Settings → Secrets and variables → Actions → New repository secret`

| Secret Name | Value |
|---|---|
| `APIFY_TOKEN` | Token API dari apify.com |
| `GEMINI_API_KEY` | API Key dari aistudio.google.com |
| `TELEGRAM_BOT_TOKEN` | Token dari @BotFather |
| `TELEGRAM_CHAT_ID` | Chat ID Telegram kamu |

### 3. Cara mendapatkan Telegram Chat ID

```bash
# Set env variable dulu
export TELEGRAM_BOT_TOKEN="token_bot_kamu"

# Jalankan
python daily_content.py get-chat-id
```

### 4. Test manual

Buka tab **Actions** di GitHub → klik **FOMI Daily Content Engine** → klik **Run workflow**.

## Biaya

- GitHub Actions: **GRATIS** (2000 menit/bulan)
- Apify: **GRATIS** (free tier $5 credit)
- Gemini API: **GRATIS** (free tier)
- Telegram Bot: **GRATIS**
