"""
FOMI MASTER BRAND KNOWLEDGE BASE (SINGLE SOURCE OF TRUTH)
=========================================================
Dokumen resmi seluruh informasi produk, formula, ekosistem XFOMI, 
after-sales, pricing, target persona, dan panduan visual FOMI.
"""

FOMI_KNOWLEDGE = {
    "brand_name": "FOMI (Foaming Hand Care)",
    "tagline": "Kunci Keaslian Sentuhan",
    
    # ─── 1. LATAR BELAKANG & FORMULA ───
    "origin_story": (
        "FOMI diciptakan dari keresahan maraknya virus/bakteri di zaman sekarang, "
        "namun sabun cuci tangan biasa di pasaran seringkali menggunakan bahan kimia keras "
        "yang membuat kulit tangan cewek jadi kering, kasar, dan kehilangan kelembapan. "
        "FOMI hadir sebagai solusi antibakteri berbahan dasar alami yang merawat kulit tangan seperti skincare."
    ),
    "key_ingredients": [
        {"name": "Eco-Enzyme", "role": "Antibakteri alami 10x lebih kuat hasil fermentasi ramah lingkungan untuk melawan kuman/virus."},
        {"name": "Premium Collagen", "role": "Menjaga elastisitas, kekenyalan, dan keremajaan kulit tangan agar tidak keriput."},
        {"name": "Natural Honey", "role": "Memberikan nutrisi alami dan kelembutan mendalam."},
        {"name": "Glycerin", "role": "Humektan/pelembap intensif pengunci hidrasi agar tangan tetap lembap seharian."}
    ],
    "aroma": {
        "name": "Royale Nectar",
        "notes": "Perpaduan mewah manis madu alami dengan sentuhan woody dan kesegaran citrus."
    },

    # ─── 2. FISIK PRODUK & UNBOXING EXPERIENCE ───
    "product_specs": {
        "shape": "Botol Kotak Estetik 100 ml (Compact, travel-friendly, aesthetic on desk/sink)",
        "cap_type": "Tutup Press Top",
        "foam_texture": "Busa lembut, tebal, mudah dibilas tanpa rasa licin atau lengket."
    },
    "unboxing_box_contents": [
        "1x Boks kemasan eksklusif FOMI",
        "1x Botol kotak FOMI 100 ml (isi sabun Royale Nectar)",
        "1x Kartu Fisik Member Xfomi Eksklusif (Hitam Gold dengan QR Code & 6 digit kode unik di belakang)",
        "1x Kartu Ucapan / Thank You Card resmi",
        "1x Lembar Stiker Ekspresi DIY FOMI (untuk konsep 'Adopt & Name Your FOMI')",
        "Bantalan jerami ramah lingkungan (eco-friendly shredded straw cushion) sebagai pengaman produk di dalam boks."
    ],

    # ─── 3. EKOSISTEM XFOMI & AFTER-SALES ───
    "xfomi_ecosystem": {
        "website_url": "https://xfomiid.web.app/",
        "platform_type": "Platform Komunitas Eksklusif & After-Sales FOMI",
        "member_identity": "XFOMI (Member Xfomi)",
        "redeem_mechanism": [
            "Step 1: Beli produk FOMI (dapat kartu member fisik hitam-gold di dalam boks).",
            "Step 2: Buka website https://xfomiid.web.app/ dan login/daftar.",
            "Step 3: Masukkan 6 digit kode unik dari bagian belakang kartu fisik ke dashboard ➔ Tiap kode = +1 Poin.",
            "Step 4: Kumpulkan 15 Poin (15x redeem kode).",
            "Step 5: Tukarkan 15 Poin menjadi 1 Voucher Shopee 'FOMI Ultimate Pack'.",
            "Step 6: Buka toko Shopee FOMI (shopee.co.id/fomiid), checkout hadiah, masukkan kode voucher ➔ Hadiah menjadi Rp 0 (GRATIS)!"
        ],
        "reward_details": (
            "Kartu Karakter Eksklusif berbahan PVC Tebal (kualitas premium sekelas kartu ATM / Kartu Timezone) "
            "bergambar karakter FOMI yang sangat bernilai koleksi."
        ),
        "level_ranking_system": [
            "Level 1: Novice Member (Syarat: 0 Voucher Ditukar - Anggota baru)",
            "Level 2: Fomi Explorer (Syarat: 1 Voucher Ditukar - Berhasil tukar 1 Ultimate Pack)",
            "Level 3: Bronze Hunter (Syarat: 2 Voucher Ditukar - Aktif mengumpulkan & menukar poin)",
            "Level 4: Silver Knight (Syarat: 4 Voucher Ditukar - Prajurit perak Xfomi)",
            "Level 5: Gold Warrior, dst. sampai 10 Level Pangkat."
        ],
        "room_chat_features": [
            "Obrolan bebas antar sesama member XFOMI.",
            "Fitur Post Foto (pamer botol FOMI yang sudah ditempel stiker & dinamai).",
            "Battle / Adu Karakter (Member yang punya kartu karakter hasil klaim Shopee bisa menantang teman untuk duel karakter di chatroom)."
        ],
        "hold_features": [
            "AR Interactive (Scan Kartu 3D) -> JANGAN DIPROMOSIKAN DULU (Masih tahap penyempurnaan).",
            "3D Open World Game Multiplayer -> JANGAN DIPROMOSIKAN DULU (Masih tahap penyempurnaan)."
        ]
    },

    # ─── 4. PRICING & CHANNEL PENJUALAN ───
    "pricing": {
        "normal_price": "Rp 49.000",
        "promo_price": "Rp 41.000 (Diskon Rp 8.000)",
        "volume": "100 ml"
    },
    "sales_channels": [
        {"platform": "Shopee", "url": "https://shopee.co.id/fomiid#product_list"},
        {"platform": "TikTok Shop", "name": "FOMI Indonesia"}
    ],

    # ─── 5. TARGET PERSONA & TONE OF VOICE ───
    "target_audience": [
        "Cewek Gen Z (usia 17–28 tahun)",
        "Anak Skena / Indie aesthetic yang suka produk berkonsep unik",
        "Mahasiswi / Anak Kost yang suka dekorasi meja & wastafel aesthetic",
        "Pencinta barang lucu, estetik, dan hobi koleksi kartu/stiker unik",
        "Orang yang peduli kebersihan tangan dari virus tapi gamau kulit tangan kering/kasar."
    ],
    "tone_of_voice": "Casual, cerdas, kreatif, bahasa anak muda Indonesia (gue/aku/kamu/lo), ceplas-ceplos, anti-kaku, seru, dan relatable."
}


def get_formatted_knowledge_prompt():
    """Mengembalikan ringkasan terformat untuk disuntikkan ke System Prompt AI."""
    k = FOMI_KNOWLEDGE
    text = f"""
═══════════════════════════════════════════════════════════════════
🏛️ FOMI MASTER BRAND KNOWLEDGE BASE (SUMBER KEBENARAN RESMI)
═══════════════════════════════════════════════════════════════════

1. IDENTITAS & FORMULA FOMI:
- Brand: {k['brand_name']} | Tagline: "{k['tagline']}"
- Latar Belakang: {k['origin_story']}
- 4 Kandungan Utama:
  • Eco-Enzyme: {k['key_ingredients'][0]['role']}
  • Premium Collagen: {k['key_ingredients'][1]['role']}
  • Natural Honey: {k['key_ingredients'][2]['role']}
  • Glycerin: {k['key_ingredients'][3]['role']}
- Aroma Khas: {k['aroma']['name']} ({k['aroma']['notes']})

2. FISIK PRODUK & UNBOXING (100ml BENTUK KOTAK):
- Bentuk Botol: {k['product_specs']['shape']} dengan {k['product_specs']['cap_type']}.
- Tekstur: {k['product_specs']['foam_texture']}
- Isi Lengkap 1 Boks FOMI:
  • 1x Boks kemasan eksklusif FOMI
  • 1x Botol kotak FOMI 100 ml (isi sabun Royale Nectar)
  • 1x Kartu Fisik Member Xfomi Eksklusif (Hitam Gold dengan QR Code & 6 digit kode unik di belakang)
  • 1x Kartu Ucapan (Thank You Card)
  • 1x Lembar Stiker Ekspresi DIY FOMI (Konsep 'Adopt & Name Your FOMI')
  • Bantalan jerami ramah lingkungan (eco-friendly shredded straw cushion) sebagai pengaman produk di dalam boks.

3. EKOSISTEM XFOMI & AFTER-SALES (https://xfomiid.web.app/):
- Nama Komunitas: Member XFOMI
- Alur Redeem 15 Poin:
  1. Beli FOMI ➔ Buka boks ➔ Ambil Kartu Fisik Member Xfomi Hitam-Gold.
  2. Buka https://xfomiid.web.app/ ➔ Masukkan 6 digit kode unik di belakang kartu ➔ Tiap kartu = +1 Poin.
  3. Kumpulkan 15 Poin ➔ Tukar jadi Kode Voucher Shopee 'FOMI Ultimate Pack'.
  4. Buka Shopee FOMI (shopee.co.id/fomiid) ➔ Checkout hadiah, masukkan kode voucher ➔ Hadiah menjadi Rp 0 (GRATIS)!
- Hadiah yang Didapat: {k['xfomi_ecosystem']['reward_details']}
- Sistem 10 Level Pangkat:
  • Level 1: Novice Member (0 voucher)
  • Level 2: Fomi Explorer (1 voucher ditukar)
  • Level 3: Bronze Hunter (2 voucher ditukar)
  • Level 4: Silver Knight (4 voucher ditukar), dst.
- Fitur Room Chat Web XFOMI:
  • Obrolan bebas sesama member XFOMI
  • Fitur Post Foto botol FOMI stiker
  • Fitur Battle / Adu Karakter antar member yang punya kartu karakter
- CATATAN KHUSUS: Fitur AR 3D Scan & 3D Open World Game JANGAN dipromosikan dulu (masih tahap penyempurnaan).

4. HARGA & TEMPAT BELI:
- Harga Normal: {k['pricing']['normal_price']} ➔ Harga Promo Saat Ini: {k['pricing']['promo_price']} (Diskon Rp 8.000).
- Toko Resmi: Shopee (shopee.co.id/fomiid) & TikTok Shop FOMI Indonesia.

5. TARGET AUDIENCE:
- Cewek Gen Z (17-28 th), Anak Skena/Indie, Mahasiswi/Anak Kost aesthetic, Kolektor barang unik/kartu/stiker, yang peduli kebersihan tanpa bikin tangan kering.
- Gaya Bahasa: {k['tone_of_voice']}
═══════════════════════════════════════════════════════════════════
"""
    return text
