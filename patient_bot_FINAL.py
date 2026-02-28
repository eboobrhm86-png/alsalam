
import logging
from typing import Dict, List

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

BOT_TOKEN = "8695538621:AAHT7z2y4ZPGbPYd-PjdrnqQSY2BggmHaww"

WARDS: List[str] = [
    "ردهة الطوارئ نساء",
    "ردهة الطوارئ رجال",
    "طابق رجال",
    "Hdu",
    "حميات نساء",
    "حميات رجال",
    "بلجيكي",
]

PATIENTS: Dict[str, List[Dict[str, str]]] = {ward: [] for ward in WARDS}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(w, callback_data=f"ward:{w}")] for w in WARDS]
    await update.message.reply_text(
        "اختر الردهة:", reply_markup=InlineKeyboardMarkup(keyboard)
    )


def ward_menu(ward_name: str):
    buttons = [
        [InlineKeyboardButton("➕ إضافة مريض", callback_data=f"add:{ward_name}")]
    ]

    for i, patient in enumerate(PATIENTS[ward_name]):
        buttons.append(
            [InlineKeyboardButton(patient["name"], callback_data=f"patient:{ward_name}:{i}")]
        )

    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back")])
    return InlineKeyboardMarkup(buttons)


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "back":
        keyboard = [[InlineKeyboardButton(w, callback_data=f"ward:{w}")] for w in WARDS]
        await query.edit_message_text(
            "اختر الردهة:", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if data.startswith("ward:"):
        ward = data.split(":", 1)[1]
        context.user_data["current_ward"] = ward
        await query.edit_message_text(
            f"الردهة: {ward}", reply_markup=ward_menu(ward)
        )
        return

    if data.startswith("add:"):
        ward = data.split(":", 1)[1]
        context.user_data["adding"] = {"ward": ward, "step": "name"}
        await query.edit_message_text("اكتب اسم المريض:")
        return

    if data.startswith("patient:"):
        _, ward, index = data.split(":")
        patient = PATIENTS[ward][int(index)]

        text = (
            f"اسم المريض: {patient['name']}\n"
            f"التوصيات: {patient['recommendation']}\n"
            f"الحالة: {patient['status']}\n"
            f"الجرعات: {patient['dosage']}"
        )

        buttons = [
            [InlineKeyboardButton("إخراج المريض", callback_data=f"remove:{ward}:{index}")],
            [InlineKeyboardButton("⬅️ رجوع", callback_data=f"ward:{ward}")],
        ]

        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(buttons))
        return

    if data.startswith("remove:"):
        _, ward, index = data.split(":")
        PATIENTS[ward].pop(int(index))
        await query.edit_message_text("تم إخراج المريض.")
        await query.message.reply_text(
            f"الردهة: {ward}", reply_markup=ward_menu(ward)
        )
        return


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "adding" not in context.user_data:
        await update.message.reply_text("استخدم /start للبدء.")
        return

    data = context.user_data["adding"]
    ward = data["ward"]

    if data["step"] == "name":
        data["name"] = update.message.text
        data["step"] = "recommendation"
        await update.message.reply_text("اكتب التوصيات:")
        return

    if data["step"] == "recommendation":
        data["recommendation"] = update.message.text
        data["step"] = "status"
        await update.message.reply_text("اكتب الحالة المرضية:")
        return

    if data["step"] == "status":
        data["status"] = update.message.text
        data["step"] = "dosage"
        await update.message.reply_text("كل كم ساعة الجرعات؟")
        return

    if data["step"] == "dosage":
        patient = {
            "name": data["name"],
            "recommendation": data["recommendation"],
            "status": data["status"],
            "dosage": update.message.text,
        }

        PATIENTS[ward].append(patient)
        del context.user_data["adding"]

        await update.message.reply_text("تمت إضافة المريض.")
        await update.message.reply_text(
            f"الردهة: {ward}", reply_markup=ward_menu(ward)
        )


def main():
    if BOT_TOKEN == "PUT_YOUR_BOT_TOKEN_HERE":
        raise RuntimeError("ضع توكن البوت داخل المتغير BOT_TOKEN")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
