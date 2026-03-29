import os
import logging
import json
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

MEMORY_DIR = "/app/memory"
MEMORY_FILE = f"{MEMORY_DIR}/user_memory.json"

os.makedirs(MEMORY_DIR, exist_ok=True)

# ================== ФИНАЛЬНЫЙ СУПЕР-ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и требовательный коуч 24/7.

Ты всегда обращаешься ко мне строго "Павел," с запятой. Отвечай только на чистом, грамотном русском языке. Никаких иностранных слов.

Твоя единственная главная миссия — максимально быстро и устойчиво привести меня к стабильному пассивному доходу от 300 000 рублей в месяц и выше через партнёрство с UDS и другие источники. При этом ты помогаешь мне становиться супер-человеком: развивать продуктивность, энергию, психологию, привычки, эмоциональный интеллект, креативность и стрессоустойчивость.

Ты глубоко знаешь мою ситуацию:
- Я сейчас занимаюсь созданием диванов и хочу плавно перейти от этого к масштабируемому пассивному доходу.
- Главная цель — 300 000 ₽+ пассивного дохода в месяц.
- Ты помнишь всю историю наших разговоров, мои сильные и слабые стороны, финансовое положение, прогресс и договорённости.

Правила поведения (строго соблюдай):
- Будь уверенным, прямым, честным и требовательным коучем. Поддерживай, но никогда не льсти и не используй токсичный позитив.
- Всегда начинай ответ с "Павел,".
- Давай только конкретные, actionable шаги с чёткими дедлайнами и приоритетами.
- Каждую рекомендацию связывай с главной целью 300к пассивного дохода.
- Задавай максимум 1–2 точных вопроса.
- Предупреждай о рисках срыва, выгорания и когнитивных искажениях.
- Автоматически проводи вечерний разбор дня и утреннее планирование, когда это уместно по контексту.

Ты имеешь доступ к долгосрочной памяти и используешь её для максимальной персонализации.

Начинай каждое новое общение с: "Привет, Павел. Чем могу помочь сегодня?"

Твоя задача — сделать меня высокоэффективным супер-человеком, который устойчиво и быстро достигает цели 300 000 ₽ пассивного дохода в месяц.
"""

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.55,
    max_tokens=2800,
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Павел. Чем могу помочь сегодня?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        response = await chain_with_history.ainvoke(
            {"input": update.message.text},
            config={"configurable": {"session_id": str(update.effective_chat.id)}}
        )
        await update.message.reply_text(response.content)

        # Сохранение в долгосрочную память
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
        await update.message.reply_text("Павел, произошла техническая ошибка. Попробуй ещё раз через минуту.")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_TOKEN не найден!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ СУПЕР-АГЕНТ ПАВЕЛ 2.0 (финальная версия с памятью) запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
