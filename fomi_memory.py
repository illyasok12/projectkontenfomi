"""
FOMI AI LEARNING & MEMORY BANK (CONTINUOUS IMPROVEMENT SYSTEM)
==============================================================
Menyimpan pola-pola yang berhasil, anti-patterns (hal yang dilarang/dihindari),
serta hasil evaluasi performa konten agar AI terus berevolusi setiap hari.
"""

import os
import json

MEMORY_FILE = os.path.join(os.path.dirname(__file__), "memory.json")

DEFAULT_MEMORY = {
    "anti_patterns": [
        "JANGAN bahas tentang tangan keriput / penuaan secara berlebihan (target audiens adalah Gen Z 17-28 tahun).",
        "JANGAN gunakan bahasa brosur atau copywriting iklan formal.",
        "JANGAN memaksakan seluruh value FOMI masuk ke dalam satu video sekaligus (fokus 1 pesan kuat per konten).",
        "JANGAN mempromosikan fitur AR 3D Scan & 3D Open World Game sampai ada instruksi lebih lanjut."
    ],
    "winning_angles": [
        "Angle Unboxing & Aesthetic: Memperlihatkan boks berjerami ramah lingkungan, botol kotak 100ml press top, dan stiker ekspresi DIY.",
        "Angle Gamifikasi XFOMI: Membahas kartu member fisik hitam-gold, sistem 15 poin di xfomiid.web.app, dan klaim kartu karakter PVC tebal gratis di Shopee.",
        "Angle Relatable Gen Z: Tangan kering/kasar karena sabun murah di cafe/tempat umum, tangan kotor sehabis naik ojol/KRL, atau tangan bau minyak sehabis kulineran.",
        "Angle Sensori Mewah: Menyoroti aroma 'Royale Nectar' (madu mewah + woody citrus) dan tekstur busa foam lembut seperti awan."
    ],
    "learned_insights": [
        "22/08/2026: Audiens Gen Z lebih tertarik pada keunikan after-sales (kartu PVC, redeem Shopee, game chat) daripada edukasi skincare medis yang kaku.",
        "22/08/2026: Variasi hook harus seimbang antara humor, keresahan sehari-hari anak muda, dan keunikan produk."
    ]
}


def load_memory():
    """Memuat memori AI dari file JSON."""
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading memory: {e}")
    return DEFAULT_MEMORY


def save_memory(memory_data):
    """Menyimpan pembaruan memori ke file JSON."""
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(memory_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving memory: {e}")
        return False


def add_feedback_to_memory(category, feedback_text):
    """
    Menambahkan catatan baru ke kategori memori (anti_patterns, winning_angles, learned_insights).
    """
    mem = load_memory()
    if category not in mem:
        mem[category] = []
    mem[category].append(feedback_text)
    save_memory(mem)
    return True


def get_formatted_memory_prompt():
    """Format memori untuk disuntikkan ke System Prompt AI."""
    mem = load_memory()
    text = f"""
═══════════════════════════════════════════════════════════════════
🧠 AI SELF-LEARNING & MEMORY BANK (CATATAN EVOLUSI KONTEN)
═══════════════════════════════════════════════════════════════════

🚫 ANTI-PATTERNS (HAL-HAL YANG DILARANG / JANGAN DIULANGI):
"""
    for item in mem.get("anti_patterns", []):
        text += f"• {item}\n"

    text += "\n🏆 WINNING ANGLES (SUDUT PANDANG TERBUKTI SUKSES & DIREKOMENDASIKAN):\n"
    for item in mem.get("winning_angles", []):
        text += f"• {item}\n"

    text += "\n💡 INSIGHT & PELAJARAN TERAKHIR:\n"
    for item in mem.get("learned_insights", []):
        text += f"• {item}\n"

    text += "═══════════════════════════════════════════════════════════════════\n"
    return text
