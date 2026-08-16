"""
FOMI Daily Content Engine
=========================
Script otomatis yang berjalan setiap hari jam 7 pagi WIB via GitHub Actions.
Alur: Scrape trending TikTok/IG → Generate konsep konten FOMI via Gemini → Kirim ke Telegram.
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta

# Pastikan UTF-8 untuk output console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# === KONFIGURASI (diambil dari GitHub Secrets / Environment Variables) ===
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

WIB = timezone(timedelta(hours=7))


# ============================================================
# BAGIAN 1: AMBIL DATA TRENDING TIKTOK VIA APIFY
# ============================================================

def get_tiktok_trending():
    """
    Menjalankan Apify actor untuk mendapatkan video TikTok trending
    di Indonesia kategori beauty/skincare/hand care.
    """
    print("[1/4] Mengambil data trending TikTok via Apify...")

    actor_id = "clockworks~tiktok-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"

    # Search query TikTok relevan dengan sabun / aesthetic lifestyle
    search_queries = [
        "sabun cuci tangan aesthetic",
        "hand wash viral",
        "skincare hand care",
    ]

    all_results = []

    payload = {
        "searchQueries": search_queries,
        "resultsPerPage": 5,
        "shouldDownloadVideos": False,
        "shouldDownloadCovers": False,
    }

    try:
        response = requests.post(
            run_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code != 201:
            print(f"  ⚠️ Gagal menjalankan TikTok actor: {response.status_code} - {response.text[:200]}")
            return all_results

        run_data = response.json()["data"]
        run_id = run_data["id"]
        print(f"  ▶ Actor TikTok berjalan (run: {run_id})")

        # Tunggu actor selesai (max 90 detik)
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        for _ in range(18):
            time.sleep(5)
            status_resp = requests.get(status_url, timeout=15)
            status = status_resp.json()["data"]["status"]
            if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break

        if status == "SUCCEEDED":
            dataset_id = run_data["defaultDatasetId"]
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit=10"
            dataset_resp = requests.get(dataset_url, timeout=15)
            items = dataset_resp.json()

            for item in items:
                all_results.append({
                    "desc": item.get("text", item.get("description", ""))[:200],
                    "author": item.get("authorMeta", {}).get("name", item.get("author", "unknown")),
                    "plays": item.get("playCount", item.get("plays", 0)),
                    "likes": item.get("diggCount", item.get("likes", 0)),
                    "shares": item.get("shareCount", item.get("shares", 0)),
                    "music": item.get("musicMeta", {}).get("musicName", item.get("music", "unknown")),
                    "hashtags": [h.get("name", h) if isinstance(h, dict) else str(h) 
                                for h in item.get("hashtags", [])[:8]],
                    "url": item.get("webVideoUrl", item.get("url", "")),
                })
            print(f"  ✅ Berhasil ambil {len(all_results)} video TikTok!")
        else:
            print(f"  ⚠️ Status akhir actor TikTok: {status}")

    except Exception as e:
        print(f"  ⚠️ Error TikTok scraper: {e}")

    print(f"  📊 Total video terkumpul: {len(all_results)}")
    return all_results


# ============================================================
# BAGIAN 2: AMBIL DATA TRENDING IG REELS VIA APIFY
# ============================================================

def get_ig_trending():
    """
    Menjalankan Apify Instagram Scraper untuk mendapatkan Reels trending
    di niche beauty/skincare Indonesia.
    """
    print("[2/4] Mengambil data trending IG Reels via Apify...")

    actor_id = "apify~instagram-scraper"
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"

    hashtags_to_search = ["sabuncucitangan", "handcare", "skincareviral", "unboxingaesthetic"]

    all_results = []

    for tag in hashtags_to_search[:2]:  # Batasi 2 agar hemat credit
        payload = {
            "search": tag,
            "searchType": "hashtag",
            "resultsLimit": 5,
            "searchLimit": 1,
        }

        try:
            response = requests.post(
                run_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code != 201:
                print(f"  ⚠️ Gagal untuk #{tag}: {response.status_code}")
                continue

            run_data = response.json()["data"]
            run_id = run_data["id"]
            print(f"  ▶ Actor berjalan untuk #{tag} (run: {run_id})")

            # Tunggu selesai
            status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
            for _ in range(24):
                time.sleep(5)
                status_resp = requests.get(status_url, timeout=15)
                status = status_resp.json()["data"]["status"]
                if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                    break

            if status != "SUCCEEDED":
                print(f"  ⚠️ Actor gagal untuk #{tag}: status={status}")
                continue

            dataset_id = run_data["defaultDatasetId"]
            dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit=5"
            dataset_resp = requests.get(dataset_url, timeout=15)
            items = dataset_resp.json()

            for item in items:
                all_results.append({
                    "hashtag": tag,
                    "caption": item.get("caption", "")[:200],
                    "owner": item.get("ownerUsername", "unknown"),
                    "likes": item.get("likesCount", 0),
                    "comments": item.get("commentsCount", 0),
                    "views": item.get("videoViewCount", item.get("videoPlayCount", 0)),
                    "url": item.get("url", ""),
                })

            print(f"  ✅ Dapat {len(items)} post untuk #{tag}")

        except Exception as e:
            print(f"  ⚠️ Error untuk #{tag}: {e}")
            continue

    print(f"  📊 Total IG posts terkumpul: {len(all_results)}")
    return all_results


# ============================================================
# BAGIAN 3: GENERATE KONSEP KONTEN FOMI VIA GEMINI AI
# ============================================================

def generate_fomi_content(tiktok_data, ig_data):
    """
    Menggunakan Gemini API untuk menghasilkan konsep konten harian FOMI
    berdasarkan data trending yang sudah dikumpulkan.
    """
    print("[3/4] Generating konsep konten FOMI via Gemini AI...")

    tanggal = datetime.now(WIB).strftime("%A, %d %B %Y")

    # Rangkum data trending menjadi konteks
    tiktok_summary = ""
    for i, v in enumerate(tiktok_data[:8], 1):
        tiktok_summary += (
            f"{i}. @{v['author']} — {v['plays']:,} plays, {v['likes']:,} likes\n"
            f"   Musik: {v['music']}\n"
            f"   Hashtags: {', '.join('#'+h for h in v['hashtags'][:5])}\n"
            f"   Isi: {v['desc'][:120]}\n"
            f"   Link: {v['url']}\n\n"
        )

    ig_summary = ""
    for i, p in enumerate(ig_data[:5], 1):
        ig_summary += (
            f"{i}. @{p['owner']} — {p['views']:,} views, {p['likes']:,} likes\n"
            f"   Caption: {p['caption'][:120]}\n"
            f"   Link: {p['url']}\n\n"
        )

    prompt = f"""Kamu adalah content strategist profesional untuk brand FOMI Indonesia.

TENTANG FOMI:
- FOMI adalah "Skincare-Infused Foaming Hand Care" (sabun cuci tangan premium berbentuk foam).
- Tagline: "Kunci Keaslian Sentuhan"
- 3 kandungan utama: Eco-Enzyme (antibakteri alami), Kolagen Premium (elastisitas kulit), Madu Alami (kelembapan).
- Keunikan: Setiap boks dilengkapi stiker ekspresi bulat DIY (•‿•, ^‿^, o_o, ◕‿↼) yang bisa ditempel di botol dan diberi nama sendiri ("Adopt & Name Your FOMI").
- Target market: Gen Z perempuan Indonesia, usia 17-28 tahun, suka hal-hal aesthetic/cute.
- Positioning: BUKAN sabun mahal/luxury. Tapi sabun yang lucu, personal, dan bikin cuci tangan jadi ritual seru.

TANGGAL HARI INI: {tanggal}

DATA TRENDING TIKTOK INDONESIA HARI INI:
{tiktok_summary if tiktok_summary else "(Data tidak tersedia hari ini)"}

DATA TRENDING IG REELS HARI INI:
{ig_summary if ig_summary else "(Data tidak tersedia hari ini)"}

TUGAS:
Berdasarkan data trending di atas, buatkan 1 konsep konten TikTok/Reels untuk FOMI hari ini.

FORMAT OUTPUT (WAJIB IKUTI PERSIS):

📅 KONSEP KONTEN FOMI — [Tanggal]

🎯 TEMA BESAR:
[Tuliskan tema besar dalam 1 kalimat hook yang sangat natural ala Gen Z, BUKAN kalimat korporat/katalog]

🎵 REKOMENDASI LAGU:
[Judul lagu — Artis] (alasan singkat kenapa cocok)

🎨 PROMPT GAMBAR AI (Slide 1 Hook):
[Tulis 1 prompt detail dalam BAHASA INGGRIS untuk AI Flux membuat foto visual mockup Slide 1 yang estetik, contoh: "Aesthetic pastel pink FOMI foaming hand soap pump bottle with cute DIY smiley face sticker, placed on a modern clean bathroom sink with soft morning sunlight, Indonesian Gen Z aesthetic, 9:16 vertical TikTok style, cinematic product photography, 8k resolution"]

📸 STORYBOARD (6-7 SLIDE):

Slide 1 (Hook):
- Foto: [deskripsi foto yang harus diambil]
- Teks di layar: "[tulisan yang harus ditempel di foto]"

Slide 2 (Curiosity):
- Foto: [deskripsi]
- Teks di layar: "[tulisan]"

Slide 3 (Reveal):
- Foto: [deskripsi]
- Teks di layar: "[tulisan]"

Slide 4 (Experience):
- Foto: [deskripsi]
- Teks di layar: "[tulisan]"

Slide 5 (Engagement/Comment Bait):
- Foto: [deskripsi]
- Teks di layar: "[tulisan]"

Slide 6 (Payoff):
- Foto: [deskripsi]
- Teks di layar: "[tulisan]"

Slide 7 (Closing/Brand):
- Foto: [deskripsi]
- Teks di layar: "[tulisan]"

✍️ CAPTION (siap copy-paste):
[Caption lengkap dengan hashtag, gaya bahasa santai ala TikTok Indonesia, BUKAN bahasa formal/AI]

💡 KENAPA KONSEP INI BISA VIRAL:
[Jelaskan 2-3 alasan kenapa konsep ini bisa kena algoritma berdasarkan data trending hari ini]

🔗 REFERENSI TRENDING HARI INI:
[Cantumkan 2-3 link video trending yang jadi inspirasi dari data di atas]

ATURAN PENTING:
1. Semua teks HARUS bergaya bahasa anak muda Indonesia (casual, pakai "gue/aku/kamu", emoji wajar, BUKAN bahasa brosur).
2. Teks di slide 1 dan makna caption HARUS saling terhubung (untuk SEO TikTok).
3. JANGAN menyebut kandungan eco-enzyme/kolagen/madu di konten ini KECUALI memang relevan dengan tren hari ini.
4. Prioritaskan aspek CUTE, AESTHETIC, dan PERSONAL (stiker, nama botol, packaging).
5. JANGAN gunakan klaim kesehatan yang tidak bisa dibuktikan.
"""

    # Model priority list (dengan automatic fallback jika salah satu overload)
    models_to_try = [
        "gemini-3.7-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
        "gemini-3.1-flash-lite",
    ]

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 3000,
        },
    }

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        print(f"  ▶ Mencoba generate dengan {model_name}...")
        
        for attempt in range(2):
            try:
                resp = requests.post(url, json=body, timeout=60)
                if resp.status_code == 200:
                    result = resp.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"  ✅ Sukses generate konten dengan {model_name}!")
                    return content
                else:
                    print(f"  ⚠️ Status {resp.status_code} pada {model_name} (percobaan {attempt+1})")
                    time.sleep(2)
            except Exception as e:
                print(f"  ⚠️ Error request {model_name}: {e}")
                time.sleep(2)

    print("  ❌ Semua model gagal merespons.")
    return None


# ============================================================
# BAGIAN 4: GENERATE GAMBAR AI & KIRIM KE TELEGRAM
# ============================================================

def generate_ai_image(image_prompt):
    """
    Menghasilkan gambar AI realistis format 9:16 (TikTok Portrait)
    menggunakan model Flux via Pollinations.ai (Gratis, HD, Tanpa Watermark).
    """
    print("[3.5/4] Generating mockup gambar AI (Flux 9:16)...")
    try:
        clean_prompt = image_prompt.strip().replace("\n", " ")
        encoded_prompt = requests.utils.quote(clean_prompt)
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=720&height=1280&nologo=true&model=flux"
        
        resp = requests.get(img_url, timeout=60)
        if resp.status_code == 200 and len(resp.content) > 5000:
            print(f"  ✅ Gambar AI berhasil dibuat ({len(resp.content):,} bytes)!")
            return resp.content
        else:
            print(f"  ⚠️ Gagal fetch gambar: status {resp.status_code}")
            return None
    except Exception as e:
        print(f"  ⚠️ Error generate gambar AI: {e}")
        return None


def send_photo_to_telegram(photo_bytes, caption):
    """Mengirim foto AI ke Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        files = {"photo": ("fomi_slide1.jpg", photo_bytes, "image/jpeg")}
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": caption[:1024],
            "parse_mode": "Markdown",
        }
        resp = requests.post(url, data=data, files=files, timeout=30)
        if resp.status_code != 200:
            data["parse_mode"] = ""
            resp = requests.post(url, data=data, files=files, timeout=30)
        
        if resp.status_code == 200:
            print("  ✅ Foto visual mockup AI terkirim ke Telegram!")
            return True
        else:
            print(f"  ⚠️ Gagal kirim foto: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  ⚠️ Error kirim foto ke Telegram: {e}")
        return False


def send_to_telegram(message):
    """Mengirim pesan teks ke Telegram bot."""
    print("[4/4] Mengirim konsep konten ke Telegram...")

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️ Telegram token/chat ID belum diset. Print ke console saja.")
        print("=" * 60)
        print(message)
        print("=" * 60)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram punya limit 4096 karakter per pesan
    chunks = []
    if len(message) <= 4000:
        chunks = [message]
    else:
        lines = message.split("\n")
        current_chunk = ""
        for line in lines:
            if len(current_chunk) + len(line) + 1 > 4000:
                chunks.append(current_chunk)
                current_chunk = line + "\n"
            else:
                current_chunk += line + "\n"
        if current_chunk:
            chunks.append(current_chunk)

    success = True
    for i, chunk in enumerate(chunks):
        try:
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }
            resp = requests.post(url, json=payload, timeout=15)

            if resp.status_code != 200:
                payload["parse_mode"] = ""
                resp = requests.post(url, json=payload, timeout=15)

            if resp.status_code == 200:
                print(f"  ✅ Pesan teks bagian {i+1}/{len(chunks)} terkirim!")
            else:
                print(f"  ⚠️ Gagal kirim teks bagian {i+1}: {resp.text[:200]}")
                success = False

            if i < len(chunks) - 1:
                time.sleep(1)

        except Exception as e:
            print(f"  ⚠️ Error kirim Telegram: {e}")
            success = False

    return success


# ============================================================
# BAGIAN 5: DAPATKAN TELEGRAM CHAT ID (UTILITY)
# ============================================================

def get_telegram_chat_id():
    """
    Utility function: jalankan ini sekali untuk mendapatkan chat ID kamu.
    Pastikan kamu sudah mengirim pesan ke bot terlebih dahulu.
    """
    if not TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN belum diset!")
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    resp = requests.get(url, timeout=10)

    if resp.status_code == 200:
        data = resp.json()
        if data["result"]:
            chat_id = data["result"][-1]["message"]["chat"]["id"]
            print(f"✅ Chat ID kamu: {chat_id}")
            print(f"   Simpan ini sebagai TELEGRAM_CHAT_ID di GitHub Secrets!")
            return chat_id
        else:
            print("❌ Belum ada pesan. Kirim pesan apa saja ke bot dulu, lalu jalankan lagi.")
    else:
        print(f"❌ Error: {resp.status_code}")

    return None


# ============================================================
# MAIN: ALUR UTAMA
# ============================================================

def main():
    tanggal = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
    print(f"\n{'='*60}")
    print(f"🫧 FOMI Daily Content Engine — {tanggal}")
    print(f"{'='*60}\n")

    # Validasi environment variables
    missing = []
    if not APIFY_TOKEN:
        missing.append("APIFY_TOKEN")
    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    if missing:
        print(f"❌ Environment variables belum diset: {', '.join(missing)}")
        print("   Set via GitHub Secrets atau export manual.")
        sys.exit(1)

    # Jika dipanggil dengan argumen "get-chat-id", jalankan utility
    if len(sys.argv) > 1 and sys.argv[1] == "get-chat-id":
        get_telegram_chat_id()
        return

    # Step 1: Ambil data trending TikTok
    tiktok_data = get_tiktok_trending()

    # Step 2: Ambil data trending IG
    ig_data = get_ig_trending()

    # Step 3: Generate konsep konten via Gemini
    if not tiktok_data and not ig_data:
        print("⚠️ Tidak ada data trending yang berhasil dikumpulkan.")
        print("   Akan generate konsep berdasarkan pengetahuan umum saja...")

    content = generate_fomi_content(tiktok_data, ig_data)

    if not content:
        print("❌ Gagal generate konten. Cek Gemini API key.")
        sys.exit(1)

    # Step 4: Generate Gambar Mockup AI & Kirim ke Telegram
    # Cari prompt gambar di dalam output Gemini
    image_prompt = ""
    if "PROMPT GAMBAR AI" in content:
        try:
            part = content.split("PROMPT GAMBAR AI")[1]
            if "📸 STORYBOARD" in part:
                part = part.split("📸 STORYBOARD")[0]
            # Bersihkan tanda kurung atau titik dua
            image_prompt = part.replace(":", "").replace("(", "").replace(")", "").strip()
            # Ambil baris pertama atau teks prompt
            lines = [l.strip() for l in image_prompt.split("\n") if l.strip() and not l.strip().startswith("[") and not l.strip().endswith("]")]
            if lines:
                image_prompt = " ".join(lines)
        except Exception as e:
            print(f"  ⚠️ Gagal parse prompt gambar: {e}")

    if not image_prompt:
        image_prompt = "Aesthetic pastel FOMI foaming hand soap bottle with cute DIY face sticker on modern bathroom sink, soft cinematic lighting, 9:16 vertical TikTok style, high quality product photo"

    print(f"  🎨 Prompt AI Image: {image_prompt[:80]}...")
    photo_bytes = generate_ai_image(image_prompt)

    # Kirim foto visual dulu ke Telegram (jika berhasil)
    if photo_bytes:
        photo_caption = f"🫧 *VISUAL MOCKUP SLIDE 1 (HOOK)*\n📅 {tanggal}\n_Generated by AI (Flux 9:16)_"
        send_photo_to_telegram(photo_bytes, photo_caption)

    # Step 5: Kirim teks konsep lengkap ke Telegram
    header = f"🫧 *FOMI DAILY CONTENT STRATEGY*\n📅 {tanggal}\n{'─'*30}\n\n"
    full_message = header + content

    send_to_telegram(full_message)

    print(f"\n{'='*60}")
    print("✅ SELESAI! Gambar AI dan Konsep Konten terkirim ke Telegram.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
