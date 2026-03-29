import os
import logging
import json
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

MEMORY_DIR = "/app/memory"
MEMORY_FILE = f"{MEMORY_DIR}/user_memory.json"
os.makedirs(MEMORY_DIR, exist_ok=True)

# ================== СУПЕР-ПРОМПТ С РИТУАЛАМИ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и очень требовательный коуч 24/7.

Ты всегда обращаешься ко мне "Павел,". Только чистый русский язык.

Главная миссия — привести меня к 300 000 ₽+ пассивного дохода в месяц через UDS и другие источники максимально быстро, но устойчиво. Одновременно помогаешь мне становиться супер-человеком (продуктивность, энергия, психология, привычки, эмоциональный интеллект, креативность).

Ты помнишь всю историю наших разговоров, мои цели, прогресс, сильные/слабые стороны и текущее положение.

Правила (строго):
- Будь прямым, честным и требовательным. Никакой воды и токсичного позитива.
- Всегда начинай ответ с "Павел,".
- Давай только конкретные шаги с дедлайнами и приоритетами.
- Связывай всё с главной целью 300к.
- Задавай максимум 1–2 вопроса.
- Автоматически проводи вечерний разбор дня и утреннее планирование, когда это уместно по времени или контексту.

Начинай общение с: "Привет, Павел. Чем могу помочь сегодня?"
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.55,
    max_tokens=3000,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

memory_store = load_memory()

def get_session_history(session_id: str):
    if session_id not in memory_store:
        memory_store[session_id] = []
    history = ChatMessageHistory()
    for msg in memory_store[session_id]:
        if msg["role"] == "user":
            history.add_user_message(msg["content"])
        else:
            history.add_ai_message(msg["content"])
    return history

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# ================== АВТОМАТИЧЕСКИЕ РИТУАЛЫ ==================
async def morning_ritual(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    await context.bot.send_message(chat_id=chat_id, text="Павел, доброе утро.\n\nДавай спланируем сегодняшний день. Какие ключевые задачи приближают тебя к 300к пассивного дохода? Какие биоритмы сегодня? Какой уровень энергии?")

async def evening_ritual(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    await context.bot.send_message(chat_id=chat_id, text="Павел, вечерний разбор дня.\n\nЧто ты сделал сегодня для цели 300к? Что пошло хорошо? Что можно улучшить завтра? Как уровень энергии и настроение?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = await chain_with_history.ainvoke(
            {"input": update.message.text},
            config={"configurable": {"session_id": str(update.effective_chat.id)}}
        )
        await update.message.reply_text(response.content)

        session_id = str(update.effective_chat.id)
        if session_id not in memory_store:
            memory_store[session_id] = []
        memory_store[session_id].append({"role": "user", "content": update.message.text})
        memory_store[session_id].append({"role": "assistant", "content": response.content})
        
        if len(memory_store[session_id]) > 200:
            memory_store[session_id] = memory_store[session_id][-200:]
        
        save_memory(memory_store)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("Павел, произошла ошибка. Попробуй ещё раз.")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_TOKEN не найден!")
        return

    app = Application.builder().token(TOKEN).build()

    # Добавляем ритуалы (примерно 8:00 утра и 22:00 вечера по Москве)
    job_queue = app.job_queue
    job_queue.run_daily(morning_ritual, time=time(8, 0), days=(0,1,2,3,4,5,6), chat_id=None)
    job_queue.run_daily(evening_ritual, time=time(22, 0), days=(0,1,2,3,4,5,6), chat_id=None)

    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("Привет, Павел. Чем могу помочь сегодня?")))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ ПАВЕЛ 2.0 — СУПЕР-АГЕНТ С РИТУАЛАМИ И ПАМЯТЬЮ запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
