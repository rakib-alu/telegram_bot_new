import os
import re
import logging
import asyncio
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext
)

# ------------------------------------
# LOAD TOKEN
# ------------------------------------
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable missing!")


# ------------------------------------
# LOGGING
# ------------------------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ------------------------------------
# POINT SYSTEM
# ------------------------------------
user_points = {}

def add_point(uid):
    user_points[uid] = user_points.get(uid, 0) + 1

def get_rank(points):
    if points >= 50:
        return "⭐ Gold Member"
    if points >= 20:
        return "🥈 Silver Member"
    if points >= 1:
        return "🥉 Bronze Member"
    return "❌ No Activity"


# ------------------------------------
# BAD WORD SYSTEM
# ------------------------------------
BAD_WORDS = []


def add_bad(update, context):
    if len(context.args) == 0:
        update.message.reply_text("⚠️ ব্যবহার: /addbad শব্দ")
        return

    word = context.args[0].lower()
    if word in BAD_WORDS:
        update.message.reply_text("⚠️ এই শব্দ আগেই list এ আছে!")
        return

    BAD_WORDS.append(word)
    update.message.reply_text(f"✅ `{word}` bad-word list এ যোগ হয়েছে!", parse_mode="Markdown")


def del_bad(update, context):
    if len(context.args) == 0:
        update.message.reply_text("⚠️ ব্যবহার: /delbad শব্দ")
        return

    word = context.args[0].lower()
    if word not in BAD_WORDS:
        update.message.reply_text("⚠️ এই শব্দ list এ নেই!")
        return

    BAD_WORDS.remove(word)
    update.message.reply_text(f"🗑 `{word}` list থেকে মুছে ফেলা হয়েছে!", parse_mode="Markdown")


def list_bad(update, context):
    if not BAD_WORDS:
        update.message.reply_text("📭 Bad word list খালি।")
        return

    words = "\n".join(f"• {w}" for w in BAD_WORDS)
    update.message.reply_text(f"📌 **Bad Words List:**\n{words}", parse_mode="Markdown")


# ------------------------------------
# AUTO CLEAN SYSTEM (BAD WORD + LINKS)
# ------------------------------------
LINK_PATTERN = r"(https?://\S+|t\.me/\S+)"

def auto_clean(update, context):
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text
    user_id = msg.from_user.id

    add_point(user_id)

    # bad words
    for word in BAD_WORDS:
        if word.lower() in text.lower():
            try:
                msg.delete()
            except:
                pass
            return

    # links
    if re.search(LINK_PATTERN, text):
        try:
            msg.delete()
        except:
            pass
        return


# ------------------------------------
# RANK COMMAND
# ------------------------------------
def rank_cmd(update, context):
    user = update.effective_user
    pts = user_points.get(user.id, 0)
    rank = get_rank(pts)

    update.message.reply_text(
        f"👤 {user.first_name}\n"
        f"📌 Points: {pts}\n"
        f"🎖 Rank: {rank}"
    )


# ------------------------------------
# WELCOME MESSAGE
# ------------------------------------
def welcome(update, context):
    if update.message.new_chat_members:
        for member in update.message.new_chat_members:
            mention = f"<a href='tg://user?id={member.id}'>{member.first_name}</a>"

            msg = (
                f"🌸 আসসালামু আলাইকুম 🌸\n\n"
                f"{mention} 💫 আপনাকে আমাদের গ্রুপে স্বাগতম!\n\n"
                f"📌 গ্রুপটি পিন করে রাখুন\n"
                f"🔔 আপডেট পেতে চ্যানেলে যোগ দিন 👇"
            )

            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url="https://t.me/CardArenaOfficial")]
            ])

            context.bot.send_message(
                chat_id=update.message.chat_id,
                text=msg,
                parse_mode="HTML",
                reply_markup=kb
            )


# ------------------------------------
# MAIN
# ------------------------------------
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    # command handlers
    dp.add_handler(CommandHandler("rank", rank_cmd))
    dp.add_handler(CommandHandler("addbad", add_bad))
    dp.add_handler(CommandHandler("delbad", del_bad))
    dp.add_handler(CommandHandler("badlist", list_bad))

    # welcome
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, welcome))

    # message filter
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, auto_clean))

    print("BOT STARTED SUCCESSFULLY…")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
