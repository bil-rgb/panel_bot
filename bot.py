import os
import re
import time
import random
import asyncio
import logging
import zipfile
import shutil
import tempfile
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.constants import ParseMode
from ai_handler import AIHandler

# ─── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["8984664004:AAFN0LMs-R17k_0yM9CFJureAyl3fMQPHB4"]
MAX_FILE_SIZE = 100 * 1024 * 1024        # 100 MB
ALLOWED_EXTENSIONS = {".zip", ".html", ".htm", ".php", ".js", ".css", ".txt"}
TEMP_DIR = Path(tempfile.gettempdir()) / "panel_bot"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

ai = AIHandler()

# ─── Helpers ───────────────────────────────────────────────────────────────────
PANEL_PATTERNS = [
    # Generic panel/porto keywords
    r'\b(admin|panel|porto|portal|dashboard|cpanel|whm|plesk)\b',
    r'(AdminLTE|Bootstrap|CoreUI|Tabler|Volt|Argon|Materialize)',
    r'\b(login|signin|register|signup)\b',
    # Copyright / branding lines
    r'(Copyright|©|Powered by|Designed by|Developed by)[^\n<"]{0,80}',
    # Title / brand in HTML
    r'<title>[^<]{1,200}</title>',
    r'(brand|logo|site-?name|app-?name)["\s:=]+["\']([^"\'<>{}\n]{1,80})["\']',
]

def find_panel_files(root: Path) -> list[Path]:
    """Recursively collect HTML, PHP, JS, CSS files."""
    result = []
    for ext in ("*.html", "*.htm", "*.php", "*.js", "*.css", "*.txt"):
        result.extend(root.rglob(ext))
    return result

def extract_panel_name(content: str) -> str | None:
    """Try to detect existing panel/brand name from file content."""
    # Title tag first
    m = re.search(r'<title>([^<]{1,100})</title>', content, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Copyright line
    m = re.search(r'(Copyright|©|Powered by)\s+\d{0,4}\s*([A-Za-z][^\n<"]{1,60})', content, re.IGNORECASE)
    if m:
        return m.group(2).strip()
    return None

async def rename_content(old_content: str, old_name: str, new_name: str) -> str:
    """Replace panel name references inside a file's text content."""
    # Direct string replacement (case-insensitive)
    new = re.sub(re.escape(old_name), new_name, old_content, flags=re.IGNORECASE)
    # Generic panel keywords → new name (optional, lighter touch)
    for pattern in [r'(?i)\bAdminLTE\b', r'(?i)\bCoreUI\b', r'(?i)\bVolt Dashboard\b']:
        if re.search(pattern, new):
            new = re.sub(pattern, new_name, new)
    return new

# ─── Rename Engine ─────────────────────────────────────────────────────────────
async def process_panel_rename(
    zip_path: Path,
    new_name: str,
    progress_cb=None
) -> Path:
    """
    Extract ZIP, rename panel references, repack, return new ZIP path.
    Uses AI to generate smart replacement suggestions when needed.
    """
    work_dir = TEMP_DIR / f"work_{int(time.time())}_{random.randint(1000,9999)}"
    work_dir.mkdir(parents=True)

    try:
        # 1. Extract
        if progress_cb:
            await progress_cb("📦 Mengekstrak file...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(work_dir)

        files = find_panel_files(work_dir)
        total = len(files)

        # 2. Detect old panel name from first HTML/PHP file
        old_name = None
        for f in files:
            try:
                raw = f.read_text(encoding="utf-8", errors="ignore")
                old_name = extract_panel_name(raw)
                if old_name:
                    break
            except Exception:
                continue

        if not old_name:
            old_name = "Admin Panel"  # fallback

        # AI: generate smart new name variant to avoid duplicate-detection issues
        ai_name = await ai.generate_panel_name(new_name)
        final_name = ai_name if ai_name else new_name

        # 3. Replace in each file
        changed = 0
        for idx, fpath in enumerate(files, 1):
            if progress_cb and idx % max(1, total // 5) == 0:
                pct = int(idx / total * 100)
                await progress_cb(f"✏️ Memproses file... {pct}% ({idx}/{total})")
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                new_content = await rename_content(content, old_name, final_name)
                if new_content != content:
                    fpath.write_text(new_content, encoding="utf-8")
                    changed += 1
            except Exception as e:
                logger.warning(f"Skip {fpath.name}: {e}")

        # 4. Repack
        if progress_cb:
            await progress_cb("🗜️ Mengemas ulang ZIP...")

        out_zip = TEMP_DIR / f"{final_name.replace(' ', '_')}_renamed.zip"
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in work_dir.rglob("*"):
                if f.is_file():
                    zf.write(f, f.relative_to(work_dir))

        return out_zip, old_name, final_name, changed, total

    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

# ─── Bot Handlers ──────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 *Selamat datang di Panel Rename Bot!*\n\n"
        "🔧 Bot ini bisa ganti nama panel/porto dari file ZIP secara otomatis.\n\n"
        "📌 *Cara Pakai:*\n"
        "1️⃣ Kirim file ZIP berisi panel/porto kamu\n"
        "2️⃣ Bot akan tanya nama baru yang kamu mau\n"
        "3️⃣ Masukkan nama baru → file siap didownload!\n\n"
        "📦 *Maks. ukuran file: 100 MB*\n"
        "🤖 *Didukung AI multi-provider untuk hasil terbaik*\n\n"
        "Kirim /help untuk bantuan lebih lanjut."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 *Panduan Panel Rename Bot*\n\n"
        "*Format file yang didukung:*\n"
        "• ZIP berisi HTML, PHP, JS, CSS\n\n"
        "*Perintah:*\n"
        "/start — Mulai bot\n"
        "/help — Panduan ini\n"
        "/cancel — Batalkan proses saat ini\n\n"
        "*Cara kerja AI:*\n"
        "Bot menggunakan beberapa AI provider (Groq, Together AI, OpenRouter) "
        "secara bergantian agar selalu bisa beroperasi tanpa error.\n\n"
        "*Tips:*\n"
        "• Pastikan file ZIP tidak rusak\n"
        "• Nama panel baru bebas, misal: `MyPortal`, `AdminX`, dll\n"
        "• File hasil rename otomatis didownload ke HP/PC kamu"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("❌ Proses dibatalkan. Kirim file baru kapan saja!")

async def handle_document(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc:
        return

    # Size check
    if doc.file_size and doc.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(
            f"❌ File terlalu besar! Maks. *100 MB*, file kamu *{doc.file_size/1024/1024:.1f} MB*.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    # Extension check
    fname = doc.file_name or ""
    ext = Path(fname).suffix.lower()
    if ext != ".zip":
        await update.message.reply_text(
            "❌ Hanya file *ZIP* yang didukung.\n"
            "Silakan ZIP dulu panel/porto kamu lalu kirim ulang.",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    msg = await update.message.reply_text("📥 Mengunduh file... mohon tunggu.")

    try:
        tg_file = await doc.get_file()
        save_path = TEMP_DIR / f"{update.effective_user.id}_{int(time.time())}.zip"
        await tg_file.download_to_drive(str(save_path))

        ctx.user_data["zip_path"] = str(save_path)
        ctx.user_data["original_name"] = fname

        await msg.edit_text(
            f"✅ File *{fname}* berhasil diunduh!\n\n"
            "📝 Sekarang kirim *nama baru* untuk panel/porto kamu:\n"
            "_(Contoh: MyDashboard, PortoXYZ, SuperAdmin)_",
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        await msg.edit_text(f"❌ Gagal mengunduh file: `{e}`", parse_mode=ParseMode.MARKDOWN)

async def handle_new_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "zip_path" not in ctx.user_data:
        await update.message.reply_text(
            "⚠️ Belum ada file. Kirim file ZIP panel/porto dulu ya!"
        )
        return

    new_name = update.message.text.strip()
    if len(new_name) < 2 or len(new_name) > 60:
        await update.message.reply_text("⚠️ Nama harus antara 2–60 karakter.")
        return

    zip_path = Path(ctx.user_data["zip_path"])
    if not zip_path.exists():
        await update.message.reply_text("❌ File tidak ditemukan, silakan kirim ulang.")
        ctx.user_data.clear()
        return

    progress_msg = await update.message.reply_text("🔄 Memulai proses rename...")

    async def update_progress(text: str):
        try:
            await progress_msg.edit_text(text)
        except Exception:
            pass

    try:
        out_zip, old_name, final_name, changed, total = await process_panel_rename(
            zip_path, new_name, update_progress
        )

        await update_progress("📤 Mengirim file hasil...")

        caption = (
            f"✅ *Rename Selesai!*\n\n"
            f"📁 Nama lama: `{old_name}`\n"
            f"🆕 Nama baru: `{final_name}`\n"
            f"📝 File diubah: *{changed}/{total}*\n\n"
            f"⬇️ Silakan download file di bawah ini!"
        )

        with open(out_zip, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=out_zip.name,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN
            )

        # Cleanup
        zip_path.unlink(missing_ok=True)
        out_zip.unlink(missing_ok=True)
        ctx.user_data.clear()

        await progress_msg.delete()

    except Exception as e:
        logger.error(f"Rename error: {e}", exc_info=True)
        await update_progress(f"❌ Gagal memproses file: `{e}`")

# ─── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_name))

    logger.info("🤖 Panel Rename Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
