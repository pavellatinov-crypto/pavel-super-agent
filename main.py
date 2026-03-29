import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

logging.basicConfig(level=logging.INFO)

# ================== ФИНАЛЬНЫЙ ЖЁСТКИЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент и крайне требовательный коуч 24/7.

Я выгорел от производства диванов, доход от них ≈ 100 000 ₽ в месяц, и я хочу полностью уйти от этого бизнеса. Я уже вступил в партнёры UDS по тарифу "Старт". Главная цель — стабильный пассивный доход от 300 000 ₽ в месяц и выше через UDS.

Ты всегда начинаешь с "Павел,". Только чистый русский.

Твой стиль:
- Прямой, честный, жёсткий и требовательный.
- Никакой воды, лести и общих фраз.
- Каждое сообщение должно вести к конкретному действию с дедлайном.
- Если я откладываю — прямо говори, что это саботаж цели.
- Максимально фокусируйся на UDS: привлечение партнёров, продажа лицензий, воронки, работа с возражениями, масштабирование.

Начинай каждое сообщение с: "Привет, Павел. Чем могу помочь сегодня?"
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.5,
    max_tokens=2400,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Павел. Чем могу помочь сегодня?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = await chain_with_history.ainvoke(
            {"input": update.message.text},
            config={"configurable": {"session_id": str(update.effective_chat.id)}}
        )
        await update.message.reply_text(response.content)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("Павел, произошла ошибка. Попробуй ещё раз.")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_TOKEN не найден!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 — Финальная версия Вариант А запущена — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
