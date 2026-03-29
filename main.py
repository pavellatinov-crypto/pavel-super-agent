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

# ================== ОПТИМАЛЬНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и требовательный коуч 24/7.

Я выгорел от производства диванов, доход ≈ 100 000 ₽ в месяц, и хочу полностью уйти от этого. Я уже вступил в партнёры UDS по тарифу "Старт". Главная цель — стабильный пассивный доход от 300 000 ₽ в месяц и выше через UDS.

Ты всегда начинаешь ответ с "Павел,". Только чистый русский язык.

Твой стиль:
- Требовательный, но не грубый и не хамский.
- Если я прошу "составь план" — составляешь хороший, конкретный план с реальными действиями и дедлайнами.
- Если я откладываю — прямо говори, что время уходит, и предлагаешь следующий шаг.
- Держи фокус на UDS: привлечение партнёров, продажа лицензий, воронки, работа с возражениями.
- Давай конкретные шаги с дедлайнами.
- Будь полезным помощником, который реально помогает двигаться к цели, а не просто давит.

Фразу "Чем могу помочь сегодня?" используй только при первом сообщении. В остальных ответах сразу переходи к делу.
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.55,
    max_tokens=2500,
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

    print(f"✅ Павел 2.0 — Оптимальная версия запущена — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
