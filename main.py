print("СТАРТ ФАЙЛА")

import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
print("TOKEN:", TOKEN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("ПОЛУЧИЛ СООБЩЕНИЕ")

    if not update.message:
        return

    if not update.message.text:
        return

    await update.message.reply_text("Я живой")

def main():
    print("ЗАШЛИ В MAIN")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()