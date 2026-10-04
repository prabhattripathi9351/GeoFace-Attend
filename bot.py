import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---------------------------------------------------------------
# Health server (Render ko port dikhane ke liye)
# Yeh sabse upar hona chahiye, run_polling() se pehle
# ---------------------------------------------------------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"GeoFace Attend bot is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), HealthHandler).serve_forever()


threading.Thread(target=start_health_server, daemon=True).start()

# ---------------------------------------------------------------
# Baaki imports
# ---------------------------------------------------------------
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

from face_utils import extract_embedding, detect_all_faces, match_against_database
from excel_utils import generate_attendance_excel
from db import save_student, get_student_by_telegram, get_all_students, get_student_count

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing!")

# States
ROLL_NUMBER, NAME, COURSE, BRANCH, YEAR, PHOTO_REG = range(6)

logging.basicConfig(level=logging.INFO)

# -------- /start --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_student_count()
    await update.message.reply_text(
        "🤖 *GeoFace Attend Bot*\n\n"
        "👨‍🎓 *Students:*\n"
        "/register - Face register karo (ek baar)\n\n"
        "👨‍🏫 *Teachers:*\n"
        "Bas apni class ki *group photo* bhejo — attendance auto mark hogi!\n\n"
        f"📊 Total Registered Students: {count}",
        parse_mode="Markdown"
    )

# -------- /cancel --------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

# -------- STUDENT REGISTRATION --------
async def register_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    existing = get_student_by_telegram(user_id)
    if existing:
        await update.message.reply_text(
            f"✅ Aap already registered ho!\n"
            f"Roll: {existing['roll_no']}\nName: {existing['name']}"
        )
        return ConversationHandler.END

    await update.message.reply_text("📝 Apna *Roll Number* likhiye:", parse_mode="Markdown")
    return ROLL_NUMBER

async def reg_roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['roll'] = update.message.text.strip()
    await update.message.reply_text("✅ Ab apna *Naam* likhiye:", parse_mode="Markdown")
    return NAME

async def reg_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("✅ Ab apna *Course* likhiye (jaise: B.Tech):", parse_mode="Markdown")
    return COURSE

async def reg_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['course'] = update.message.text.strip()
    await update.message.reply_text("✅ Ab apni *Branch* likhiye (jaise: CSE / AIML):", parse_mode="Markdown")
    return BRANCH

async def reg_branch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['branch'] = update.message.text.strip()
    await update.message.reply_text("✅ Ab apna *Year* likhiye (1 / 2 / 3 / 4):", parse_mode="Markdown")
    return YEAR

async def reg_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        year = int(update.message.text.strip())
        if year not in [1, 2, 3, 4]:
            raise ValueError
        context.user_data['year'] = year
        await update.message.reply_text("✅ Ab apni *Selfie* bhejo (front face clear):", parse_mode="Markdown")
        return PHOTO_REG
    except:
        await update.message.reply_text("❌ Sirf 1, 2, 3, ya 4 likhiye:")
        return YEAR

async def reg_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if get_student_by_telegram(user_id):
        await update.message.reply_text("⚠️ Already registered!")
        return ConversationHandler.END

    msg = await update.message.reply_text("🔍 Face process kar raha hoon...")

    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
        embedding = extract_embedding(bytes(image_bytes))
    except Exception as e:
        await msg.edit_text(f"❌ Photo error: {e}")
        return PHOTO_REG

    if embedding is None:
        await msg.edit_text("❌ Face nahi mila! Clear selfie bhejo.")
        return PHOTO_REG

    try:
        save_student(
            context.user_data['roll'],
            context.user_data['name'],
            user_id,
            embedding,
            course=context.user_data.get('course', ''),
            branch=context.user_data.get('branch', ''),
            year=context.user_data.get('year', 0)
        )
        count = get_student_count()
        await msg.edit_text(
            f"✅ *Registration Successful!*\n\n"
            f"👤 Name: {context.user_data['name']}\n"
            f"🎫 Roll: {context.user_data['roll']}\n"
            f"📚 Course: {context.user_data['course']}\n"
            f"🏛 Branch: {context.user_data['branch']}\n"
            f"📅 Year: {context.user_data['year']}\n\n"
            f"📊 Total Registered: {count}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await msg.edit_text(f"❌ DB Error: {e}")

    return ConversationHandler.END

# -------- TEACHER: GROUP PHOTO ATTENDANCE --------
async def handle_group_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Teacher jab bhi group photo bhejega, yeh trigger hoga"""
    if not update.message.photo:
        return

    msg = await update.message.reply_text("🔍 Group photo process kar raha hoon...\n\n_Step 1: Photo download_")

    try:
        photo_file = await update.message.photo[-1].get_file()
        image_bytes = await photo_file.download_as_bytearray()
    except Exception as e:
        await msg.edit_text(f"❌ Photo error: {e}")
        return

    await msg.edit_text("🔍 _Step 2: Faces detect kar raha hoon..._", parse_mode="Markdown")

    locations, encodings = detect_all_faces(bytes(image_bytes))

    if not encodings:
        await msg.edit_text(
            "❌ Photo mein koi face nahi mila!\n\n"
            "Tips:\n"
            "• Acchi lighting\n"
            "• Saare students camera ki taraf\n"
            "• Clear photo"
        )
        return

    await msg.edit_text(
        f"✅ {len(encodings)} faces detect hue!\n\n"
        f"_Step 3: Database se match kar raha hoon..._",
        parse_mode="Markdown"
    )

    students = get_all_students()
    if not students:
        await msg.edit_text("❌ Koi student registered nahi hai!")
        return

    matched, unmatched = match_against_database(encodings, students)

    if not matched:
        await msg.edit_text(
            f"❌ Koi face match nahi hua!\n\n"
            f"Detected: {len(encodings)}\n"
            f"Matched: 0"
        )
        return

    await msg.edit_text(
        f"✅ {len(matched)} students match hue!\n"
        f"❌ {len(unmatched)} unknown\n\n"
        f"_Step 4: Excel ban raha hai..._",
        parse_mode="Markdown"
    )

    # Generate Excel
    excel_buffer, count = generate_attendance_excel(matched)

    now = datetime.now()
    filename = f"attendance_{now.strftime('%Y%m%d_%H%M')}.xlsx"

    await update.message.reply_document(
        document=excel_buffer,
        filename=filename,
        caption=(
            f"📊 *Attendance Report Ready!*\n\n"
            f"✅ Present: {len(matched)} students\n"
            f"❌ Unknown faces: {len(unmatched)}\n"
            f"👥 Total Detected: {len(encodings)}\n"
            f"📅 {now.strftime('%d %b %Y')} | 🕐 {now.strftime('%H:%M')}\n\n"
            f"Excel file upar download karo 👆"
        ),
        parse_mode="Markdown"
    )

# -------- /status --------
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    count = get_student_count()
    await update.message.reply_text(
        f"📊 *Bot Status*\n\n"
        f"👥 Total Registered Students: {count}\n\n"
        f"👨‍🏫 Teachers: Bas group photo bhejo, attendance auto hogi!",
        parse_mode="Markdown"
    )

# -------- MAIN --------
if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cancel", cancel))

    # Student Registration
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("register", register_start)],
        states={
            ROLL_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_roll)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_name)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_course)],
            BRANCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_branch)],
            YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, reg_year)],
            PHOTO_REG: [MessageHandler(filters.PHOTO, reg_photo)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(reg_conv)

    # Group Photo Handler (Any photo directly = attendance)
    app.add_handler(MessageHandler(filters.PHOTO, handle_group_photo), group=1)

    print("=" * 50)
    print("🤖 GeoFace Attend Bot Started!")
    print("📌 Students: /register")
    print("📌 Teachers: Bas group photo bhejo")
    print("=" * 50)
    app.run_polling()