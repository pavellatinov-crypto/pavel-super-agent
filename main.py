import os
import logging
from datetime import datetime, time
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, JobQueue

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

logging.basicConfig(level=logging.INFO)

# ================== ФИНАЛЬНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и крайне требовательный коуч 24/7.

Я выгорел от производства диванов, доход ≈ 100 000 ₽ в месяц, и хочу полностью уйти от этого бизнеса. Я уже в партнёрах UDS по тарифу "Старт". Главная цель — стабильный пассивный доход от 300 000 ₽ в месяц и выше через UDS.

Ты всегда обращаешься ко мне "Павел,". Только чистый русский язык.

Стиль:
- Прямой, честный, жёсткий и требовательный.
- Никакой воды и лести.
- Давай конкретные шаги с чёткими дедлайнами.
- Если я откладываю — прямо говори об этом.
- Фокус на UDS: привлечение партнёров, продажа лицензий, воронки, работа с возражениями.

Фразу "Привет, Павел. Чем могу помочь сегодня?" используй **только** при первом сообщении или после долгого перерыва. В остальных ответах сразу переходи к делу.
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.5,
    max_tokens=2600,
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

async def morning_ritual(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Павел, доброе утро.\n\nДавай спланируем день. Какие 3 ключевые задачи сегодня приближают тебя к 300к пассивного дохода через UDS? Какой уровень энергии? Какие дедлайны ставим на сегодня?"
    )

async def evening_ritual(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Павел, вечерний разбор.\n\nЧто ты сделал сегодня для цели 300к через UDS? Что пошло хорошо? Что можно улучшить завтра? Как уровень энергии и настроение? Какие задачи на завтра?"
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

    # Автоматические ритуалы по Челябинску (UTC+5)
    # Утро в 7:00, вечер в 22:00
    job_queue = app.job_queue
    job_queue.run_daily(morning_ritual, time=time(7, 0), days=(0,1,2,3,4,5,6), chat_id=None)
    job_queue.run_daily(evening_ritual, time=time(22, 0), days=(0,1,2,3,4,5,6), chat_id=None)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 с автоматическими ритуалами запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
