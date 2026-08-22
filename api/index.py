"""
FOMI 2-Way Interactive Telegram Bot (Vercel Serverless Webhook Handler)
========================================================================
Fitur:
- Chatting 2 arah dengan Senior Content Strategist FOMI AI (Gemini 3.7 / 3.5 Flash)
- Generate Foto Mockup dengan Google Imagen 3 (Nano Banana Pro) / Flux Fallback
- Generate Prompt & Panduan Video Sinematik Veo 3.1 - Quality
- Perintah Cepat: /video, /foto, /image, /veo, /hook, /help
"""

import os
import json
import base64
import requests
from http.server import BaseHTTPRequestHandler

# === KONFIGURASI ENVIRONMENT ===
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "") or os.environ.get("GEMINI_APT_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Import knowledge base
try:
    from fomi_knowledge import get_formatted_knowledge_prompt, FOMI_KNOWLEDGE
    FOMI_MASTER_INFO = get_formatted_knowledge_prompt()
except:
    FOMI_MASTER_INFO = ""

# Brand Identity FOMI
FOMI_SYSTEM_PROMPT = f"""Kamu adalah Asisten AI Senior Content Strategist & Copywriter resmi untuk brand FOMI Indonesia.

{FOMI_MASTER_INFO}

KEMAMPUAN UTAMA KAMU:
1. Menjawab pertanyaan strategi konten, ide video/foto, hook TikTok, copywriting, caption SEO, dan hashtag.
2. Membuat naskah storytelling polarisasi (Hook Negatif ➔ Konter Fakta ➔ Reveal FOMI / XFOMI ➔ Emosi ➔ CTA).
3. Menjelaskan ekosistem after-sales FOMI secara detail (kartu member fisik hitam-gold, sistem 15 poin di xfomiid.web.app, 10 level pangkat, klaim hadiah kartu karakter PVC tebal di Shopee, dan battle karakter di room chat).
4. Mengetahui fisik produk asli secara presisi: Botol bentuk KOTAK 100 ml tutup press top, aroma Royale Nectar (madu mewah + woody citrus), unboxing boks berjerami ramah lingkungan + stiker ekspresi DIY.
5. Memberikan arahan prompt visual presisi untuk Google Imagen 3 (Nano Banana Pro) dan prompt sinematik untuk Google Veo 3.1 - Quality.
6. Memberikan feedback dan revisi naskah secara instan.

PENTING / GUARDRAIL:
- Fitur AR 3D Scan & 3D Open World Game JANGAN dipromosikan dulu (masih tahap penyempurnaan).
"""


# ============================================================
# HELPER: TELEGRAM API
# ============================================================

def send_telegram_message(chat_id, text, parse_mode="Markdown"):
    """Mengirim pesan teks ke Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # Split jika pesan terlalu panjang (> 4000 karakter)
    chunks = []
    if len(text) <= 4000:
        chunks = [text]
    else:
        lines = text.split("\n")
        curr = ""
        for line in lines:
            if len(curr) + len(line) + 1 > 4000:
                chunks.append(curr)
                curr = line + "\n"
            else:
                curr += line + "\n"
        if curr:
            chunks.append(curr)

    for chunk in chunks:
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code != 200:
            payload["parse_mode"] = ""  # fallback tanpa markdown jika ada parse error
            requests.post(url, json=payload, timeout=15)
    return True


def send_telegram_photo(chat_id, photo_bytes, caption=""):
    """Mengirim file foto (bytes) ke Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    try:
        files = {"photo": ("fomi_image.jpg", photo_bytes, "image/jpeg")}
        data = {
            "chat_id": chat_id,
            "caption": caption[:1024],
            "parse_mode": "Markdown",
        }
        resp = requests.post(url, data=data, files=files, timeout=30)
        if resp.status_code != 200:
            data["parse_mode"] = ""
            resp = requests.post(url, data=data, files=files, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        print(f"Error send photo: {e}")
        return False


def send_chat_action(chat_id, action="typing"):
    """Mengirim status 'typing' atau 'upload_photo' ke Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
    try:
        requests.post(url, json={"chat_id": chat_id, "action": action}, timeout=5)
    except:
        pass


# ============================================================
# AI: GEMINI TEXT GENERATION (3.7 / 3.5 FLASH)
# ============================================================

def call_gemini_text(prompt, system_instruction=FOMI_SYSTEM_PROMPT):
    """Memanggil Gemini API untuk penalaran, copywriting, dan strategi."""
    if not GEMINI_API_KEY:
        return "⚠️ Error: `GEMINI_API_KEY` belum diset di server."

    models = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-flash-latest", "gemini-3.1-flash-lite"]
    
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 4000,
        },
    }

    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            resp = requests.post(url, json=body, timeout=60)
            if resp.status_code == 200:
                result = resp.json()
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Gemini error on {model}: {e}")
            continue

    return "⚠️ Maaf, server AI sedang sibuk. Silakan coba kirim pesan lagi dalam beberapa saat."


# ============================================================
# AI: NANO BANANA PRO (GOOGLE IMAGEN 3) + FLUX FALLBACK
# ============================================================

def generate_nano_banana_image(prompt):
    """
    Menghasilkan gambar visual mockup 9:16 menggunakan:
    1. Google Imagen 3 (Nano Banana Pro)
    2. Fallback ke Pollinations Flux jika Imagen 3 quota/key restricted
    """
    # 1. Coba Google Imagen 3 (Nano Banana Pro)
    if GEMINI_API_KEY:
        imagen_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "9:16",
                "outputMimeType": "image/jpeg",
            }
        }
        try:
            resp = requests.post(imagen_url, json=payload, timeout=45)
            if resp.status_code == 200:
                data = resp.json()
                b64_img = data["predictions"][0]["bytesBase64Encoded"]
                img_bytes = base64.b64decode(b64_img)
                return img_bytes, "Google Imagen 3 (Nano Banana Pro)"
        except Exception as e:
            print(f"Imagen 3 error: {e}, falling back to Flux...")

    # 2. Fallback ke Flux (Pollinations)
    try:
        clean_p = prompt.strip().replace("\n", " ")
        encoded = requests.utils.quote(clean_p)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=720&height=1280&nologo=true&model=flux"
        resp = requests.get(url, timeout=45)
        if resp.status_code == 200 and len(resp.content) > 5000:
            return resp.content, "Flux.1 AI"
    except Exception as e:
        print(f"Flux error: {e}")

    return None, None


# ============================================================
# LOGIKA HANDLER PERINTAH & CHAT
# ============================================================

def handle_user_message(chat_id, user_text, user_name=""):
    """Memproses pesan masuk dari user Telegram dan mengirimkan respons."""
    text_clean = user_text.strip()
    
    # 1. COMMAND: /start ATAU /help
    if text_clean in ("/start", "/help", "help", "halo", "hai"):
        msg = (
            f"👋 *Halo {user_name}! Aku FOMI Content Assistant AI.* 🫧✨\n\n"
            f"Aku siap bantu kamu 24/7 buat bikin konten viral FOMI kapan aja tanpa nunggu jam 7 pagi.\n\n"
            f"🛠 *Perintah Cepat yang Bisa Kamu Pakai:*\n\n"
            f"🎬 `/video [topik]`\n"
            f"└ Buat naskah video storytelling polarisasi + petunjuk shot & backsound.\n\n"
            f"📸 `/foto [topik]`\n"
            f"└ Buat konsep foto carousel 6 slide + visual mockup AI (Nano Banana Pro).\n\n"
            f"🎨 `/image [deskripsi visual]`\n"
            f"└ Generate gambar mockup produk aesthetic dengan *Nano Banana Pro (Imagen 3)*.\n\n"
            f"🎥 `/veo [ide adegan]`\n"
            f"└ Buatkan prompt video sinematik khusus untuk *Google Veo 3.1 - Quality*.\n\n"
            f"🪝 `/hook [topik]`\n"
            f"└ Minta 5 ide hook polarisasi (negatif ➔ konter) yang bikin stop scroll.\n\n"
            f"💬 *Atau langsung chat bebas aja!* Misal:\n"
            f"_\"Revisi naskah tadi biar lebih kocak dong\"_\n"
            f"_\"Kira-kira angle stiker DIY cocok gak buat mahasiswi?\"_"
        )
        send_telegram_message(chat_id, msg)
        return

    # 2. COMMAND: /video [topik]
    if text_clean.startswith("/video"):
        topic = text_clean.replace("/video", "", 1).strip()
        if not topic:
            send_telegram_message(chat_id, "⚠️ Masukkan topiknya ya!\nContoh: `/video sabun cuci tangan bikin kulit kering`")
            return
        
        send_chat_action(chat_id, "typing")
        send_telegram_message(chat_id, f"🎬 *Sedang menyusun naskah video storytelling polarisasi untuk topik:* _{topic}_...\n⏳ Mohon tunggu sebentar...")
        
        prompt = f"""Buatkan 1 brief naskah video storytelling polarisasi lengkap untuk FOMI dengan topik: '{topic}'.
Gunakan format storytelling 5 babak:
1. HOOK (0-3s) - Polarisasi / Negatif / Kontroversial yang bikin berhenti scroll.
2. BUILD-UP (4-15s) - Pendalaman masalah / rasa penasaran penonton.
3. REVEAL / PLOT TWIST (16-35s) - Sudut pandang baru / pembuktian FOMI.
4. PAYOFF EMOSIONAL (36-55s) - Bikin penonton merasa/kagum.
5. CTA (56-65s) - Comment bait yang memancing komentar.

Sertakan juga:
- Petunjuk visual shot-by-shot & tips rekam HP.
- Rekomendasi 2 background music (volume kecil).
- Prompt sinematik untuk Google Veo 3.1 - Quality (b-roll produk).
- Caption TikTok/Reels SEO & Hashtag siap copy-paste.
"""
        response_text = call_gemini_text(prompt)
        send_telegram_message(chat_id, f"🎬 *NASKAH VIDEO STORYTELLING FOMI*\n📌 Topik: _{topic}_\n{'─'*30}\n\n" + response_text)
        return

    # 3. COMMAND: /foto [topik]
    if text_clean.startswith("/foto"):
        topic = text_clean.replace("/foto", "", 1).strip()
        if not topic:
            send_telegram_message(chat_id, "⚠️ Masukkan topiknya ya!\nContoh: `/foto unboxing stiker bulat DIY fomi`")
            return
        
        send_chat_action(chat_id, "typing")
        send_telegram_message(chat_id, f"📸 *Sedang merancang konsep foto carousel 6 slide & visual mockup untuk topik:* _{topic}_...")
        
        prompt = f"""Buatkan 1 konsep konten foto carousel 6 slide TikTok/IG untuk FOMI dengan topik: '{topic}'.
Format:
- Slide 1: Hook foto + Text on image (bikin penasaran).
- Slide 2: Problem / Fenomena nyata.
- Slide 3: Fakta / Edukasi / Reveal.
- Slide 4: Solusi FOMI (Eco-enzyme / Stiker DIY / Foaming).
- Slide 5: Aesthetic & Lifestyle proof.
- Slide 6: CTA / Pertanyaan penutup.
- Caption & Hashtags.
- Berikan 1 PROMPT VISUAL BAHASA INGGRIS di baris paling bawah diawali dengan 'IMAGE_PROMPT: [prompt photorealistic 9:16 untuk Slide 1]'
"""
        response_text = call_gemini_text(prompt)
        
        # Ekstrak image prompt jika ada
        img_prompt = ""
        if "IMAGE_PROMPT:" in response_text:
            parts = response_text.split("IMAGE_PROMPT:")
            response_text = parts[0].strip()
            img_prompt = parts[1].strip()
        else:
            img_prompt = f"Aesthetic photorealistic vertical 9:16 shot of cute FOMI foaming hand wash bottle with round cute expression sticker on clean modern bathroom sink, natural morning window light, high resolution, 8k"

        # Kirim teks konsep
        send_telegram_message(chat_id, f"📸 *KONSEP FOTO CAROUSEL FOMI*\n📌 Topik: _{topic}_\n{'─'*30}\n\n" + response_text)
        
        # Generate gambar Slide 1 dengan Nano Banana Pro / Flux
        send_chat_action(chat_id, "upload_photo")
        img_bytes, engine_name = generate_nano_banana_image(img_prompt)
        if img_bytes:
            caption = f"🎨 *VISUAL MOCKUP SLIDE 1 (HOOK)*\n✨ Engine: _{engine_name}_\n📌 Topik: {topic}"
            send_telegram_photo(chat_id, img_bytes, caption)
        return

    # 4. COMMAND: /image [deskripsi]
    if text_clean.startswith("/image") or text_clean.startswith("/mockup"):
        desc = text_clean.replace("/image", "", 1).replace("/mockup", "", 1).strip()
        if not desc:
            send_telegram_message(chat_id, "⚠️ Masukkan deskripsi gambarnya!\nContoh: `/image botol fomi dengan stiker senyum di meja cafe estetik dekat jendela`")
            return
        
        send_chat_action(chat_id, "upload_photo")
        send_telegram_message(chat_id, f"🎨 *Sedang membuat visual mockup dengan Nano Banana Pro (Google Imagen 3)...*\nPrompt: _{desc}_")
        
        # Optimize prompt via Gemini
        enhanced_prompt = call_gemini_text(
            f"Convert this image idea into a highly detailed, photorealistic 9:16 vertical image prompt in English for product photography of cute aesthetic foam hand wash: '{desc}'. Output ONLY the prompt string.",
            system_instruction="You are an expert AI prompt engineer."
        ).strip().replace('"', '')
        
        img_bytes, engine_name = generate_nano_banana_image(enhanced_prompt)
        if img_bytes:
            caption = f"🖼️ *HASIL VISUAL MOCKUP AI*\n✨ Engine: _{engine_name}_\n📝 Deskripsi: {desc}"
            send_telegram_photo(chat_id, img_bytes, caption)
        else:
            send_telegram_message(chat_id, "⚠️ Gagal menghasilkan gambar. Silakan coba prompt lain.")
        return

    # 5. COMMAND: /veo [ide adegan]
    if text_clean.startswith("/veo"):
        desc = text_clean.replace("/veo", "", 1).strip()
        if not desc:
            send_telegram_message(chat_id, "⚠️ Masukkan ide adegan videonya!\nContoh: `/veo close up busa foam fomi keluar dari pump dengan gerakan slow motion sinematik`")
            return
        
        send_chat_action(chat_id, "typing")
        prompt = f"""Sebagai visual director, rancang 2 PROMPT VIDEO SINEMATIK SPESIALISASI GOOGLE VEO 3.1 - QUALITY untuk adegan berikut: '{desc}'.

Format output:
1. 🎬 **VEO 3.1 PROMPT (ENGLISH - Siap Copy-Paste ke Veo)**:
   - Camera: [e.g., 50mm Macro Lens, Slow Pan, Tilt-up, 4K, 60fps]
   - Lighting: [e.g., Golden hour sunlight streaming through window, soft diffusion]
   - Subject & Action: [Detail gerakan busa, tangan, botol FOMI, ekspresi stiker]
   - Motion & Physics: [Fluid dynamic foam viscosity, micro droplets, smooth 120fps slow-motion]
   - Negative Prompt: [low quality, blurry, distorted, jerky motion]

2. 💡 **PANDUAN EKSEKUSI KAMERA (Jika direkam manual pakai HP)**:
   - Posisi HP & Angle
   - Pencahayaan & Pacing
"""
        res = call_gemini_text(prompt)
        send_telegram_message(chat_id, f"🎥 *PROMPT & ARAHAN GOOGLE VEO 3.1 - QUALITY*\n📌 Ide: _{desc}_\n{'─'*30}\n\n" + res)
        return

    # 6. COMMAND: /hook [topik]
    if text_clean.startswith("/hook"):
        topic = text_clean.replace("/hook", "", 1).strip()
        if not topic:
            topic = "Sabun cuci tangan dan perawatan kulit tangan Gen Z"
        
        send_chat_action(chat_id, "typing")
        prompt = f"""Buatkan 5 IDE HOOK POLARISASI (Negatif ➔ Konter Fakta) untuk konten FOMI tentang '{topic}'.
Karakteristik:
- Bahasa anak muda Indonesia yang sangat natural, ceplas-ceplos, BUKAN bahasa iklan.
- Membuka dengan statement kontroversial/negatif yang bikin orang kaget & berhenti scroll dalam 3 detik pertama.
- Sertakan penjelasan kenapa hook ini bakal memicu perdebatan/interaksi di kolom komentar.
"""
        res = call_gemini_text(prompt)
        send_telegram_message(chat_id, f"🪝 *5 IDE HOOK POLARISASI FOMI*\n📌 Topik: _{topic}_\n{'─'*30}\n\n" + res)
        return

    # 7. CHAT BEBAS / REVISI / DISKUSI UMUM
    send_chat_action(chat_id, "typing")
    reply = call_gemini_text(f"User berkata: '{text_clean}'. Balaslah sebagai Content Strategist FOMI yang ramah, kreatif, dan solutif.")
    send_telegram_message(chat_id, reply)


# ============================================================
# VERCEL SERVERLESS HTTP HANDLER
# ============================================================

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "online", "service": "FOMI Interactive Telegram Webhook", "model": "Gemini 3.7 + Imagen 3 + Veo 3.1"}
        self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            update = json.loads(post_data.decode('utf-8'))
            
            # Cek apakah ada message masuk
            if "message" in update and "text" in update["message"]:
                msg = update["message"]
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                user_name = msg.get("from", {}).get("first_name", "Kak")
                
                # Proses pesan
                handle_user_message(chat_id, text, user_name)
                
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True}).encode('utf-8'))
            
        except Exception as e:
            print(f"Error handling webhook POST: {e}")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode('utf-8'))
