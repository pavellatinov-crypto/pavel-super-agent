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

# ================== ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент и требовательный коуч 24/7.

Я выгорел от диванов, доход ≈ 100 000 ₽, уже в партнёрах UDS по тарифу "Старт". Главная цель — 300 000 ₽+ пассивного дохода в месяц через UDS.

Ты всегда начинаешь ответ с "Павел,". Только чистый русский.

Стиль:
- Требовательный, но полезный и конструктивный.
- Давай конкретные шаги с дедлайнами.
- Если я откладываю — мягко, но прямо напоминай о цели.
- Фокус на UDS: привлечение партнёров, продажа лицензий, воронки, работа с возражениями.

Фразу "Чем могу помочь сегодня?" используй только при первом сообщении.
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

# ================== СТАБИЛЬНЫЕ РИТУАЛЫ ==================
async def morning_ritual(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Павел, доброе утро.\n\nДавай спланируем день.\n\n1. Какие 2–3 ключевые задачи сегодня приближают тебя к 300к через UDS?\n2. Какой уровень энергии сегодня?\n3. Какие дедлайны ставим на сегодня?"
    )

async def evening_ritual(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    await context.bot.send_message(
        chat_id=chat_id,
        text="Павел, вечерний разбор.\n\n1. Что ты сделал сегодня для цели 300к через UDS?\n2. Что пошло хорошо, а что можно улучшить?\n3. Как уровень энергии и настроение?\n4. Какие задачи ставим на завтра?"
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

    # Ритуалы по Челябинску (UTC+5)
    job_queue = app.job_queue
    if job_queue:
        try:
            job_queue.run_daily(morning_ritual, time=time(7, 0), days=(0,1,2,3,4,5,6), chat_id=None)
            job_queue.run_daily(evening_ritual, time=time(22, 0), days=(0,1,2,3,4,5,6), chat_id=None)
            print("Ритуалы успешно запланированы (7:00 и 22:00)")
        except Exception as e:
            logging.error(f"Ошибка планирования ритуалов: {e}")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 с стабильными ритуалами запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
