async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("ПОЛУЧИЛ СООБЩЕНИЕ")

    if not update.message:
        return

    if not update.message.text:
        return

    await update.message.reply_text("Я живой")