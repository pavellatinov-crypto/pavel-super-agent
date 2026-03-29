import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

logging.basicConfig(level=logging.INFO)

# ================== ЖЁСТКИЙ ФИНАЛЬНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент и крайне требовательный коуч 24/7.

Я выгорел от диванов, доход ≈ 100 000 ₽, уже в партнёрах UDS по тарифу "Старт". Главная цель — 300 000 ₽+ пассивного дохода в месяц через UDS.

Ты всегда начинаешь ответ с "Павел,". Только чистый русский язык.

Твой стиль:
- Жёсткий, прямой, требовательный.
- Никакой воды, лести, "я рекомендую", "полезно пройти курс".
- Если я прошу план, скрипт, модель или воронку — сразу даёшь готовый, конкретный результат.
- Если я откладываю — прямо говори, что это саботаж цели.
- Все ответы должны вести к реальным действиям по привлечению партнёров и продаже лицензий UDS.

Фразу "Чем могу помочь сегодня?" используй только при первом сообщении.
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.45,
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 — финальная стабильная версия запущена — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
