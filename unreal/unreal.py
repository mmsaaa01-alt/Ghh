
import json
from pathlib import Path
import asyncio
import re
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------- CONFIG ----------
TOKEN = "8336984787:AAH7x9HMmrWq_zBMrHRFyt3R48qmCkbLdfc"
SECRET_PASSWORD = "nealnga"
SECRET_GROUP_ID = -1003227589284

BASE = Path(__file__).resolve().parent
AUTH_FILE = BASE / "heyfam.bozo"
MAX_AUTH = 10

# store last message bot SENT (for /new)
last_sent_message = {}

# ---------- AUTH HELPERS ----------
def load_auths():
    if not AUTH_FILE.exists():
        return []
    try:
        return json.loads(AUTH_FILE.read_text(encoding="utf-8") or "[]")
    except:
        return []

def save_auths(lst):
    try:
        AUTH_FILE.write_text(json.dumps(lst, indent=2), encoding="utf-8")
    except:
        pass

# ---------- CLEAN TEXT ----------
def clean_text(text: str):
    """Removes old decorations and returns clean text with one clickable block"""
    if not text:
        text = ""

    # Remove any previous decoration blocks or duplicates
    pattern = r'(\[=+\]\s*\n?\s*@Unreal_Gods\s*\n?\s*\[=+\])'
    text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove stray @Unreal_Gods
    text = re.sub(r'@Unreal_Gods', '', text, flags=re.IGNORECASE)

    # Remove other usernames
    text = re.sub(r'@\w+', '', text)

    # Fix multiple spaces and strip
    text = re.sub(r' {2,}', ' ', text).strip()

    # Final decoration block (clickable, safe for Telegram HTML)
    deco = (
        "[=====================]\n"
        '<a href="https://t.me/Unreal_Gods">@Unreal_Gods</a>\n'
        "[=====================]"
    )

    if text:
        return f"{text}\n\n{deco}"
    else:
        return deco

# ---------- /auth ----------
async def auth(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    uid = update.effective_user.id
    try: await msg.delete()
    except: pass

    if not context.args:
        return

    auths = load_auths()
    if uid in auths or len(auths) >= MAX_AUTH:
        return

    if context.args[0] == SECRET_PASSWORD:
        auths.append(uid)
        save_auths(auths)

# ---------- /new (EDIT last message) ----------
async def new_caption(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in load_auths() or uid not in last_sent_message:
        return

    raw_text = update.message.text.replace("/new", "", 1).strip()
    new_caption = clean_text(raw_text)

    target = last_sent_message[uid]

    try:
        if target.text:
            await context.bot.edit_message_text(
                chat_id=target.chat_id,
                message_id=target.message_id,
                text=new_caption,
                parse_mode="HTML"
            )
        else:
            await context.bot.edit_message_caption(
                chat_id=target.chat_id,
                message_id=target.message_id,
                caption=new_caption,
                parse_mode="HTML"
            )
    except:
        pass

    try: await update.message.delete()
    except: pass

# ---------- MAIN MESSAGE PROCESSOR ----------
async def process_message(msg, context):
    uid = msg.from_user.id
    sent = None

    # Determine caption
    raw_caption = msg.caption if msg.caption else msg.text if msg.text else ""
    new_caption = clean_text(raw_caption)

    try:
        # Text only
        if msg.text and not msg.photo:
            sent = await msg.reply_text(new_caption, parse_mode="HTML")

        # Media with or without caption
        elif msg.photo:
            sent = await msg.reply_photo(msg.photo[-1].file_id, caption=new_caption, parse_mode="HTML")
        elif msg.document:
            sent = await msg.reply_document(msg.document.file_id, caption=new_caption, parse_mode="HTML")
        elif msg.video:
            sent = await msg.reply_video(msg.video.file_id, caption=new_caption, parse_mode="HTML")
        elif msg.voice:
            sent = await msg.reply_voice(msg.voice.file_id, caption=new_caption, parse_mode="HTML")
        elif msg.animation:
            sent = await msg.reply_animation(msg.animation.file_id, caption=new_caption, parse_mode="HTML")
        elif msg.audio:
            sent = await msg.reply_audio(msg.audio.file_id, caption=new_caption, parse_mode="HTML")

        # Sticker
        elif msg.sticker:
            sent = await msg.reply_sticker(msg.sticker.file_id)

    except Exception as e:
        print("❌ Error sending message:", e)

    # Save last sent
    last_sent_message[uid] = sent

    # Delete original
    try: await msg.delete()
    except: pass

    # Copy to secret group
    try:
        if sent: await sent.copy(SECRET_GROUP_ID)
    except: pass

# ---------- QUEUE ----------
processing_queue = asyncio.Queue()
processing_task = None

async def queue_worker(context):
    while True:
        msg = await processing_queue.get()
        await process_message(msg, context)
        processing_queue.task_done()

async def remove_forward_tag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    uid = msg.from_user.id
    if uid not in load_auths():
        return
    await processing_queue.put(msg)
    global processing_task
    if processing_task is None or processing_task.done():
        processing_task = asyncio.create_task(queue_worker(context))

# ---------- /id ----------
async def show_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in load_auths(): return
    await update.message.reply_text(str(update.effective_chat.id), parse_mode="HTML")

# ---------- MAIN ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("auth", auth))
    app.add_handler(CommandHandler("new", new_caption))
    app.add_handler(CommandHandler("id", show_id))
    app.add_handler(MessageHandler(filters.FORWARDED, remove_forward_tag))
    print("🤫 Bot running fast… with safe HTML decorations ⚡")
    app.run_polling()

if __name__ == "__main__":
    main()