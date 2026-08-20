"""
FOMI Video Storytelling Content Engine
======================================
Pipeline otomatis 9 langkah yang setiap hari:
1. Scrape akun storytelling viral (TikTok + IG) via Apify
2. Identifikasi pola viral (hook, narasi, behavior komentar)
3. Scrape topik hype hari ini
4. Hubungkan hype ke FOMI
5. Buat naskah storytelling + step-by-step video
6. Sisipkan value FOMI (jika relevan)
7. Carikan backsound/musik
8. Buat caption + hashtag
9. Sertakan referensi konten viral
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta

# UTF-8 untuk Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# === KONFIGURASI ===
APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

WIB = timezone(timedelta(hours=7))

# Seed akun storytelling yang sudah teridentifikasi viral
SEED_TIKTOK_PROFILES = [
    "happsbox",
]
SEED_IG_PROFILES = [
    "valeskasimo",
]


# ============================================================
# UTILITY: JALANKAN APIFY ACTOR & TUNGGU HASILNYA
# ============================================================

def run_apify_actor(actor_id, payload, label="actor", max_wait=120):
    """
    Menjalankan Apify actor, menunggu selesai, dan mengembalikan hasil dataset.
    """
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs?token={APIFY_TOKEN}"

    try:
        resp = requests.post(run_url, json=payload, headers={"Content-Type": "application/json"}, timeout=30)
        if resp.status_code != 201:
            print(f"    ⚠️ Gagal jalankan {label}: {resp.status_code} - {resp.text[:200]}")
            return []

        run_data = resp.json()["data"]
        run_id = run_data["id"]
        dataset_id = run_data["defaultDatasetId"]
        print(f"    ▶ {label} berjalan (run: {run_id})")

        # Tunggu selesai
        status_url = f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}"
        intervals = max_wait // 5
        for _ in range(intervals):
            time.sleep(5)
            s = requests.get(status_url, timeout=15).json()["data"]["status"]
            if s in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
                break

        if s != "SUCCEEDED":
            print(f"    ⚠️ {label} selesai dengan status: {s}")
            return []

        # Ambil hasil
        items_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}&limit=30"
        items = requests.get(items_url, timeout=15).json()
        print(f"    ✅ {label}: {len(items)} item")
        return items

    except Exception as e:
        print(f"    ⚠️ Error {label}: {e}")
        return []


# ============================================================
# STEP 1: SCRAPE AKUN STORYTELLING VIRAL
# ============================================================

def step1_scrape_storytelling_creators():
    """
    Scrape video terbaru dari akun storytelling viral di TikTok & IG.
    Mengumpulkan data performa (views, likes, comments) untuk analisa.
    """
    print("\n[STEP 1/9] Scraping akun storytelling viral...")
    all_videos = []

    # --- TikTok Profile Scraper ---
    for username in SEED_TIKTOK_PROFILES:
        print(f"  📱 TikTok @{username}...")
        items = run_apify_actor(
            "clockworks~tiktok-profile-scraper",
            {
                "profiles": [f"https://www.tiktok.com/@{username}"],
                "resultsPerPage": 8,
                "shouldDownloadVideos": False,
                "shouldDownloadCovers": False,
            },
            label=f"TikTok @{username}",
            max_wait=90,
        )
        for item in items:
            views = item.get("playCount", item.get("plays", 0))
            if views and views > 10000:  # Hanya ambil yang lumayan viral
                all_videos.append({
                    "platform": "tiktok",
                    "author": username,
                    "desc": item.get("text", item.get("description", ""))[:300],
                    "views": views,
                    "likes": item.get("diggCount", item.get("likes", 0)),
                    "comments": item.get("commentCount", item.get("comments", 0)),
                    "shares": item.get("shareCount", item.get("shares", 0)),
                    "music": item.get("musicMeta", {}).get("musicName", item.get("music", "")),
                    "url": item.get("webVideoUrl", item.get("url", "")),
                    "id": item.get("id", ""),
                })

    # --- Instagram Profile Scraper ---
    for username in SEED_IG_PROFILES:
        print(f"  📷 Instagram @{username}...")
        items = run_apify_actor(
            "apify~instagram-scraper",
            {
                "directUrls": [f"https://www.instagram.com/{username}/"],
                "resultsType": "posts",
                "resultsLimit": 8,
            },
            label=f"IG @{username}",
            max_wait=90,
        )
        for item in items:
            views = item.get("videoPlayCount", item.get("videoViewCount", 0))
            likes = item.get("likesCount", 0)
            if (views and views > 10000) or (likes and likes > 1000):
                all_videos.append({
                    "platform": "instagram",
                    "author": username,
                    "desc": item.get("caption", "")[:300],
                    "views": views or 0,
                    "likes": likes,
                    "comments": item.get("commentsCount", 0),
                    "shares": 0,
                    "music": "",
                    "url": item.get("url", ""),
                    "id": item.get("id", ""),
                })

    # Urutkan dari views tertinggi
    all_videos.sort(key=lambda x: x["views"], reverse=True)
    print(f"  📊 Total video storytelling viral terkumpul: {len(all_videos)}")
    return all_videos


# ============================================================
# STEP 2: IDENTIFIKASI POLA VIRAL + SCRAPE KOMENTAR
# ============================================================

def step2_identify_viral_patterns(videos):
    """
    Scrape komentar dari video paling viral + analisa pola dengan AI.
    """
    print("\n[STEP 2/9] Mengidentifikasi pola viral + scrape komentar...")
    comments_data = []

    # Ambil komentar dari 2 video TikTok paling viral
    tiktok_videos = [v for v in videos if v["platform"] == "tiktok" and v.get("url")]
    for v in tiktok_videos[:2]:
        print(f"  💬 Scraping komentar dari @{v['author']} ({v['views']:,} views)...")
        items = run_apify_actor(
            "clockworks~tiktok-comments-scraper",
            {
                "postURLs": [v["url"]],
                "commentsPerPost": 20,
            },
            label=f"Komentar @{v['author']}",
            max_wait=60,
        )
        for c in items:
            comments_data.append({
                "video_author": v["author"],
                "video_url": v["url"],
                "comment_text": c.get("text", c.get("comment", ""))[:200],
                "comment_likes": c.get("diggCount", c.get("likes", 0)),
            })

    print(f"  📊 Total komentar terkumpul: {len(comments_data)}")
    return comments_data


# ============================================================
# STEP 3: SCRAPE TOPIK HYPE HARI INI
# ============================================================

def step3_scrape_trending_topics():
    """
    Scrape TikTok & IG untuk mencari topik yang sedang ramai hari ini.
    """
    print("\n[STEP 3/9] Scraping topik hype hari ini...")
    trending_data = []

    # TikTok search: topik umum yang lagi ramai
    search_queries = [
        "viral hari ini indonesia",
        "berita terbaru heboh",
        "sabun tangan bahaya bakteri",
    ]

    items = run_apify_actor(
        "clockworks~tiktok-scraper",
        {
            "searchQueries": search_queries,
            "resultsPerPage": 5,
            "shouldDownloadVideos": False,
            "shouldDownloadCovers": False,
        },
        label="TikTok Trending Search",
        max_wait=90,
    )

    for item in items:
        trending_data.append({
            "desc": item.get("text", item.get("description", ""))[:300],
            "views": item.get("playCount", item.get("plays", 0)),
            "likes": item.get("diggCount", item.get("likes", 0)),
            "comments": item.get("commentCount", item.get("comments", 0)),
            "music": item.get("musicMeta", {}).get("musicName", item.get("music", "")),
            "hashtags": [h.get("name", h) if isinstance(h, dict) else str(h)
                        for h in item.get("hashtags", [])[:8]],
            "url": item.get("webVideoUrl", item.get("url", "")),
            "author": item.get("authorMeta", {}).get("name", item.get("author", "")),
        })

    print(f"  📊 Total video trending terkumpul: {len(trending_data)}")
    return trending_data


# ============================================================
# STEP 4–9: GENERATE FULL BRIEF VIA GEMINI AI
# ============================================================

def generate_full_video_brief(storytelling_videos, comments_data, trending_data):
    """
    Menggunakan Gemini AI untuk menghasilkan:
    - Analisa pola viral (Step 2 lanjutan)
    - Koneksi hype → FOMI (Step 4)
    - Naskah storytelling lengkap (Step 5)
    - Value FOMI jika relevan (Step 6)
    - Backsound recommendation (Step 7)
    - Caption + hashtag (Step 8)
    - Referensi konten viral (Step 9)
    """
    print("\n[STEP 4-9] Generating full video storytelling brief via Gemini AI...")

    tanggal = datetime.now(WIB).strftime("%A, %d %B %Y")

    # Format data untuk prompt
    vid_summary = ""
    for i, v in enumerate(storytelling_videos[:8], 1):
        vid_summary += (
            f"{i}. [{v['platform'].upper()}] @{v['author']} — {v['views']:,} views, "
            f"{v['likes']:,} likes, {v['comments']:,} comments\n"
            f"   Caption: {v['desc'][:150]}\n"
            f"   Musik: {v['music']}\n"
            f"   Link: {v['url']}\n\n"
        )

    comments_summary = ""
    for i, c in enumerate(comments_data[:15], 1):
        comments_summary += (
            f"{i}. [Video @{c['video_author']}] ({c['comment_likes']} likes): "
            f"{c['comment_text'][:120]}\n"
        )

    trending_summary = ""
    for i, t in enumerate(trending_data[:8], 1):
        trending_summary += (
            f"{i}. @{t['author']} — {t['views']:,} views\n"
            f"   Isi: {t['desc'][:150]}\n"
            f"   Hashtags: {', '.join('#'+h for h in t['hashtags'][:5])}\n"
            f"   Link: {t['url']}\n\n"
        )

    prompt = f"""Kamu adalah senior content strategist dan scriptwriter profesional untuk brand FOMI Indonesia.

═══════════════════════════════════════════
TENTANG FOMI
═══════════════════════════════════════════
- FOMI = "Skincare-Infused Foaming Hand Care" (sabun cuci tangan premium foam).
- Tagline: "Kunci Keaslian Sentuhan"
- 3 kandungan: Eco-Enzyme (antibakteri alami), Kolagen Premium, Madu Alami.
- Keunikan: Stiker ekspresi bulat DIY (•‿•, ^‿^, o_o) di setiap boks, bisa ditempel di botol & diberi nama ("Adopt & Name Your FOMI").
- Target: Gen Z perempuan Indonesia, 17-28 tahun, suka aesthetic/cute.
- Positioning: Sabun lucu, personal, bikin cuci tangan jadi ritual seru.
- Dibentuk untuk: (1) Melawan virus/bakteri dengan eco-enzyme alami, (2) Komunitas dengan game after-sales, (3) Kemasan aesthetic + stiker DIY untuk cewek & anak skena.

═══════════════════════════════════════════
KONSEP VIDEO: STORYTELLING DENGAN POLARISASI
═══════════════════════════════════════════
Format: Video real (bukan foto carousel). Kreator merekam sendiri (talking head + B-roll).
Gaya: Storytelling yang ujung-ujungnya membahas FOMI, TAPI hook-nya dimulai dari hal negatif/kontroversial/polarisasi untuk menarik perhatian, lalu di-konter dengan alasan kuat yang mengarah ke FOMI.
Tujuan: Membuat penonton BERHENTI scroll, MERASA emosi (penasaran/terkejut/setuju), dan KOMENTAR.
Backsound: Musik latar volume kecil (bukan lagu utama). Bisa lagu, bisa ambient/lo-fi, tergantung mood konten.

═══════════════════════════════════════════
TANGGAL HARI INI: {tanggal}
═══════════════════════════════════════════

═══════════════════════════════════════════
DATA 1: VIDEO STORYTELLING VIRAL DARI KREATOR REFERENSI
═══════════════════════════════════════════
{vid_summary if vid_summary else "(Data tidak tersedia)"}

═══════════════════════════════════════════
DATA 2: BEHAVIOR KOMENTAR PENONTON (Dari Video Viral di Atas)
═══════════════════════════════════════════
{comments_summary if comments_summary else "(Data tidak tersedia)"}

═══════════════════════════════════════════
DATA 3: TOPIK YANG SEDANG VIRAL/HYPE HARI INI DI TIKTOK INDONESIA
═══════════════════════════════════════════
{trending_summary if trending_summary else "(Data tidak tersedia)"}

═══════════════════════════════════════════
TUGAS BESAR: BUATKAN 1 BRIEF VIDEO STORYTELLING FOMI HARI INI
═══════════════════════════════════════════

Ikuti format output berikut PERSIS:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 BRIEF VIDEO STORYTELLING FOMI — {tanggal}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ANALISA POLA VIRAL HARI INI:
[Dari data kreator referensi di atas, identifikasi 3-4 pola yang membuat konten mereka viral: tipe hook, struktur narasi, pacing, behavior komentar]

📌 TOPIK HYPE TERPILIH:
[Pilih 1 topik dari data trending yang paling bisa disambungkan ke FOMI]
Kenapa topik ini: [alasan]

🔗 JEMBATAN HYPE → FOMI:
[Jelaskan bagaimana topik ini bisa dihubungkan ke narasi FOMI]

🎭 ANGLE POLARISASI:
Hook Negatif: "[Statement negatif/kontroversial yang jadi pembuka]"
Konter: "[Argumen balik yang mengarahkan ke FOMI]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 NASKAH VIDEO STORYTELLING
⏱️ Durasi Target: [45-90 detik]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔴 HOOK (0-3 detik) — WAJIB BIKIN BERHENTI SCROLL
Narasi: "[Kalimat pembuka provokatif/negatif — HARUS bahasa anak muda Indonesia yang natural, BUKAN bahasa brosur]"
Visual: [Deskripsi shot yang harus direkam: angle, ekspresi, latar]
Tip Rekam: [Catatan teknis singkat]

🟡 BUILD-UP (4-15 detik) — BANGUN PENASARAN
Narasi: "[Kalimat yang memperdalam masalah, buat makin penasaran]"
Visual: [Deskripsi shot]
Tip Rekam: [Catatan teknis]

🟢 REVEAL / PLOT TWIST (16-35 detik) — BALIKKAN EKSPEKTASI
Narasi: "[Ungkap sudut pandang baru / fakta mengejutkan yang membalikkan hook negatif]"
Visual: [Deskripsi shot — termasuk B-roll produk FOMI jika relevan]
Tip Rekam: [Catatan teknis]

🔵 PAYOFF EMOSIONAL (36-55 detik) — BIKIN MERASA
Narasi: "[Kalimat emosional — bisa humor, haru, bangga, atau takjub]"
Visual: [Deskripsi shot]
Tip Rekam: [Catatan teknis]

🟣 CTA / COMMENT BAIT (56-65 detik) — PANCING INTERAKSI
Narasi: "[Pertanyaan atau ajakan yang MEMAKSA orang komen]"
Visual: [Deskripsi shot]
Tip Rekam: [Catatan teknis]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💎 VALUE FOMI YANG DISISIPKAN:
[Sebutkan value FOMI mana yang relevan dengan topik hari ini. Jika TIDAK ADA yang relevan, tulis: "Tidak ada value FOMI yang dipaksakan hari ini — konten fokus pada brand awareness via storytelling."]

🎥 GOOGLE VEO 3.1 - QUALITY (CINEMATIC B-ROLL PROMPT):
[Buatkan 1 prompt sinematik Bahasa Inggris siap copy-paste ke Google Veo 3.1 - Quality untuk membuat video B-roll produk FOMI yang aesthetic/ultra-realistic 9:16]
- Camera & Lens: [misal: Macro 50mm, 4K, 60fps slow pan]
- Lighting & Atmosphere: [misal: Golden hour warm window light, aesthetic cleanroom vibe]
- Action & Motion: [misal: Rich foaming soap dispensed onto hand with cute sticker bottle in background, fluid dynamic foam physics]
- Negative Prompt: [low quality, blur, grainy, distorted]

🎵 BACKSOUND RECOMMENDATION (3 Opsi):
1. [Judul — Artis/Tipe] ⭐ Paling Direkomendasikan
   Mood: [Calm/Tense/Emotional/Upbeat]
   Kenapa cocok: [...]
   Catatan: Volume kecil, sebagai latar narasi saja

2. [Judul — Artis/Tipe]
   Mood: [...]
   Kenapa cocok: [...]

3. [Judul — Artis/Tipe]
   Mood: [...]
   Kenapa cocok: [...]

✍️ CAPTION (siap copy-paste):
[Caption yang selaras dengan hook video. Bahasa anak muda. BUKAN bahasa AI/formal. Keyword pencarian TikTok harus ada di caption.]

#️⃣ HASHTAG:
[Hashtag niche + trending + volume besar, masing-masing dikategorikan]

🔗 REFERENSI YANG DIGUNAKAN:

1. REFERENSI HOOK & GAYA PENYAMPAIAN:
   - @[akun] — [deskripsi konten] — [views] views
     Link: [URL]
     Apa yang diambil: [Teknik hook/penyampaian apa yang ditiru]

2. REFERENSI TOPIK HYPE:
   - [Video/post yang jadi sumber topik]
     Link: [URL]

3. REFERENSI BEHAVIOR KOMENTAR:
   - Komentar terbanyak bertema: [...]
   - Emosi dominan penonton: [...]
   - Strategi memancing komen serupa: [...]

ATURAN WAJIB:
1. Semua narasi HARUS bahasa anak muda Indonesia yang natural (casual, pakai "gue/aku/kamu/lo", bukan bahasa brosur/AI).
2. Narasi TIDAK BOLEH flat — harus ada naik-turun emosi (marah → penasaran → takjub → humor).
3. Hook 3 detik pertama HARUS provokatif/kontroversial (bukan "hai guys hari ini aku mau...").
4. Jangan memaksakan semua value FOMI masuk ke setiap konten. Hanya sisipkan yang relevan.
5. Visual/shot harus REALISTIS (bisa direkam pakai HP sendiri di rumah/kamar).
6. Backsound adalah musik latar volume kecil, bukan lagu utama. Bisa ambient, lo-fi, atau lagu pelan.
"""

    # Model priority
    models = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 5000,
        },
    }

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        print(f"  ▶ Mencoba {model}...")
        for attempt in range(2):
            try:
                resp = requests.post(url, json=body, timeout=90)
                if resp.status_code == 200:
                    result = resp.json()
                    content = result["candidates"][0]["content"]["parts"][0]["text"]
                    print(f"  ✅ Brief berhasil di-generate dengan {model}!")
                    return content
                else:
                    print(f"  ⚠️ Status {resp.status_code} pada {model} (attempt {attempt+1})")
                    time.sleep(3)
            except Exception as e:
                print(f"  ⚠️ Error {model}: {e}")
                time.sleep(3)

    print("  ❌ Semua model gagal.")
    return None


# ============================================================
# TELEGRAM: KIRIM BRIEF
# ============================================================

def send_to_telegram(message):
    """Kirim pesan teks ke Telegram (dengan auto-split jika terlalu panjang)."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("  ⚠️ Telegram belum dikonfigurasi. Output ke console:")
        print("=" * 60)
        print(message)
        print("=" * 60)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Split jika lebih dari 4000 karakter
    chunks = []
    if len(message) <= 4000:
        chunks = [message]
    else:
        lines = message.split("\n")
        current = ""
        for line in lines:
            if len(current) + len(line) + 1 > 4000:
                chunks.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current:
            chunks.append(current)

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
                print(f"  ✅ Pesan bagian {i+1}/{len(chunks)} terkirim!")
            else:
                print(f"  ⚠️ Gagal kirim bagian {i+1}: {resp.text[:200]}")
                success = False

            if i < len(chunks) - 1:
                time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ Error Telegram: {e}")
            success = False

    return success


# ============================================================
# MAIN
# ============================================================

def main():
    tanggal = datetime.now(WIB).strftime("%d/%m/%Y %H:%M WIB")
    print(f"\n{'='*60}")
    print(f"🎬 FOMI Video Storytelling Engine — {tanggal}")
    print(f"{'='*60}")

    # Validasi
    missing = []
    if not APIFY_TOKEN: missing.append("APIFY_TOKEN")
    if not GEMINI_API_KEY: missing.append("GEMINI_API_KEY")
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    # Step 1: Scrape akun storytelling viral
    storytelling_videos = step1_scrape_storytelling_creators()

    # Step 2: Identifikasi pola viral + scrape komentar
    comments_data = step2_identify_viral_patterns(storytelling_videos)

    # Step 3: Scrape topik hype hari ini
    trending_data = step3_scrape_trending_topics()

    # Step 4-9: Generate full brief via Gemini AI
    if not storytelling_videos and not trending_data:
        print("⚠️ Tidak ada data terkumpul. Generate berdasarkan pengetahuan umum...")

    brief = generate_full_video_brief(storytelling_videos, comments_data, trending_data)

    if not brief:
        print("❌ Gagal generate brief.")
        sys.exit(1)

    # Kirim ke Telegram
    print("\n[KIRIM] Mengirim brief ke Telegram...")
    header = (
        f"🎬 *FOMI VIDEO STORYTELLING BRIEF*\n"
        f"📅 {tanggal}\n"
        f"{'─'*30}\n\n"
    )
    send_to_telegram(header + brief)

    print(f"\n{'='*60}")
    print("✅ SELESAI! Brief video storytelling terkirim ke Telegram.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
