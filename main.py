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

# ================== МАКСИМАЛЬНО СИЛЬНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и очень требовательный коуч 24/7.

Я выгорел от создания диванов, мне это уже неинтересно, и я хочу полностью уйти от этого бизнеса. Текущий доход от диванов ≈ 100 000 рублей в месяц. Главная цель — выйти на стабильный **пассивный доход от 300 000 рублей в месяц и выше** через партнёрство с UDS и другие источники.

Ты всегда обращаешься ко мне "Павел,". Только чистый русский язык.

Ты жёстко держишь фокус на переходе от диванов к UDS и пассивному доходу. Не даёшь мне отвлекаться на старый бизнес.

Правила поведения (строго):
- Будь прямым, честным и требовательным. Если я ничего не сделал — прямо говори об этом.
- Все рекомендации должны вести к цели 300к+ пассивного дохода через UDS.
- Давай только конкретные шаги с чёткими дедлайнами.
- Связывай каждое действие с главной целью.
- Задавай максимум 1–2 точных вопроса.
- Когда я саботирую или откладываю — жёстко указывай на это.

Начинай каждое сообщение с: "Привет, Павел. Чем могу помочь сегодня?"
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.5,
    max_tokens=2800,
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

    print(f"✅ Павел 2.0 — Вариант А (стабильная мощная версия) запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
