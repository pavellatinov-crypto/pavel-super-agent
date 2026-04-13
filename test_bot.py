from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from telegram.ext import ApplicationBuilder, MessageHandler, filters

TOKEN = "ТВОЙ_TELEGRAM_TOKEN"


async def handle(update, context):
    text = update.message.text.lower()

    if text == "/start":
        context.user_data.clear()
        await update.message.reply_text("Привет! Напиши: стратегия или контент")

    elif "стратегия" in text:
        context.user_data["mode"] = "strategy"
        await update.message.reply_text("Ок, ты в режиме стратегии. Опиши бизнес")

   elif context.user_data.get("mode") == "strategy":

    if "history" not in context.user_data:
        context.user_data["history"] = []

    context.user_data["history"].append({
        "role": "user",
        "content": text
    })

    messages = [
        {"role": "system", "content": "Ты сильный бизнес-стратег. Сначала задай 1-2 уточняющих вопроса, потом дай стратегию."}
    ] + context.user_data["history"]

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )

    answer = response.choices[0].message.content

    context.user_data["history"].append({
        "role": "assistant",
        "content": answer
    })

    await update.message.reply_text(answer)

    else:
        await update.message.reply_text("Напиши, что тебе нужно")


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT, handle))

app.run_polling()