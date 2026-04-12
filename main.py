print("СТАРТ ФАЙЛА")

import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
print("TOKEN:", TOKEN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    print("ПОЛУЧИЛ:", text)

    if "привет" in text:
        await update.message.reply_text("Привет! Чем могу помочь?")
    
    elif "цена" in text:
        await update.message.reply_text("Стоимость зависит от задачи. Опиши подробнее 👇")

    elif "агент" in text:
        await update.message.reply_text("Я могу анализировать, писать стратегию и контент 🚀")

    else:
        await update.message.reply_text("Напиши, что тебе нужно — помогу разобраться 👍")
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