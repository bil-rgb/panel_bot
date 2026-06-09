# 🤖 Panel Rename Bot

Bot Telegram otomatis untuk mengganti nama panel/porto dari file ZIP. Didukung **multi-AI provider** agar tidak error, dan mendukung file hingga **100 MB**.

---

## ✨ Fitur

- 📦 Upload file ZIP panel/porto langsung via Telegram
- 🔄 Otomatis deteksi nama panel lama
- 🤖 AI multi-provider (Groq, Together AI, OpenRouter) dengan fallback otomatis
- ✏️ Rename semua referensi nama di HTML, PHP, JS, CSS, TXT
- 📤 Download file ZIP hasil rename langsung di Telegram
- 🚀 Jalan 24/7 via GitHub Actions (GRATIS!)
- 📁 Support file hingga **100 MB**

---

## 🚀 Cara Setup (Langkah demi Langkah)

### 1. Buat Bot Telegram

1. Buka [@BotFather](https://t.me/BotFather) di Telegram
2. Kirim `/newbot`
3. Ikuti instruksi → catat **BOT_TOKEN** yang diberikan

### 2. Dapatkan API Key AI (minimal 1)

| Provider | Link Daftar | Keterangan |
|----------|-------------|------------|
| **Groq** | https://console.groq.com | ✅ GRATIS, cepat |
| **Together AI** | https://api.together.xyz | ✅ GRATIS $25 kredit |
| **OpenRouter** | https://openrouter.ai | ✅ Ada model gratis |

> **Tips:** Daftar semua 3 provider agar bot tidak pernah error!

### 3. Fork / Upload ke GitHub

1. Buat repo baru di https://github.com/new
2. Upload semua file ini ke repo tersebut
3. Atau klik **Fork** jika ini sudah repo template

### 4. Set GitHub Secrets

Di repo GitHub kamu → **Settings → Secrets and variables → Actions → New repository secret**

Tambahkan secret berikut:

| Secret Name | Nilai | Wajib? |
|-------------|-------|--------|
| `BOT_TOKEN` | Token dari BotFather | ✅ WAJIB |
| `GROQ_API_KEY` | API key Groq | Minimal 1 |
| `TOGETHER_API_KEY` | API key Together AI | Minimal 1 |
| `OPENROUTER_API_KEY` | API key OpenRouter | Minimal 1 |

### 5. Aktifkan GitHub Actions

1. Di repo GitHub → klik tab **Actions**
2. Klik **"I understand my workflows, go ahead and enable them"**
3. Pilih workflow **"Panel Rename Bot"**
4. Klik **"Run workflow"** → **"Run workflow"**

Bot langsung aktif! 🎉

---

## 📱 Cara Pakai Bot

1. Buka bot kamu di Telegram
2. Kirim `/start`
3. **Kirim file ZIP** panel/porto kamu (maks. 100 MB)
4. Bot akan tanya nama baru → **ketik nama yang kamu inginkan**
5. Tunggu proses selesai → **download file ZIP hasil rename**

---

## 🔧 Struktur File

```
panel-rename-bot/
├── bot.py              # Bot Telegram utama
├── ai_handler.py       # Handler multi-AI provider
├── requirements.txt    # Dependencies Python
├── .github/
│   └── workflows/
│       └── bot.yml     # GitHub Actions workflow
└── README.md           # Panduan ini
```

---

## ⚙️ GitHub Actions — Cara Kerja

- Bot berjalan otomatis setiap push ke `main`
- Restart otomatis setiap **6 jam** (batas GitHub Actions)
- Bisa di-restart manual kapan saja via tab Actions
- **GRATIS** untuk repo public (2000 menit/bulan untuk private)

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Bot tidak merespons | Cek BOT_TOKEN di Secrets |
| AI tidak bekerja | Pastikan minimal 1 API key AI terisi |
| File gagal diupload | Pastikan format ZIP dan ukuran < 100 MB |
| Workflow tidak jalan | Aktifkan Actions di Settings → Actions → General |

---

## 📝 Lisensi

MIT License — Bebas digunakan dan dimodifikasi.
