import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from graph import graph

TOKEN = os.getenv("TELEGRAM_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("ПОЛУЧИЛ СООБЩЕНИЕ")

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text    text = update.message.text

    state = {
        "user_input": text,
        "analysis": "",
        "strategy": "",
        "content": "",
        "goal": "выйти на 300000 рублей в месяц через UDS"
    }

    result = graph.invoke(state)

    answer = f"""
АНАЛИЗ:
{result["analysis"]}

СТРАТЕГИЯ:
{result["strategy"]}

КОНТЕНТ:
{result["content"]}
"""

    await update.message.reply_text(answer)

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()