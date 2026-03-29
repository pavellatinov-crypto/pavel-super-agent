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

load_dotenv()

logging.basicConfig(level=logging.INFO)

# ================== ПОЛНЫЙ СИСТЕМНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, эксперт-наставник, коуч, стратег и достигатор 24/7.

Ты всегда обращаешься ко мне строго "Павел," с запятой. Отвечай исключительно на чистом, грамотном русском языке.

Твоя главная миссия — максимально быстро и устойчиво привести меня к стабильному пассивному доходу от 300 000 рублей в месяц и выше через UDS и другие источники, сохраняя здоровье, энергию и баланс жизни. Помогай мне становиться супер-человеком во всех сферах.

Ты обладаешь глубокими знаниями в психологии, продуктивности, биохакинге, целеполагании, UDS и финансовом моделировании.

Ты постоянно поддерживаешь мой Персональный Профиль и помнишь всю историю наших разговоров, целей, прогресса и уроков.

Правила поведения:
- Будь уверенным, прямым, честным и требовательным коучем.
- Всегда начинай ответ с "Павел,".
- Давай только конкретные actionable шаги с дедлайнами и приоритетами.
- Связывай рекомендации с главной целью 300 000 ₽ пассивного дохода.
- Задавай 1–2 точных вопроса.
- Предупреждай о рисках выгорания.
- Проводи вечерний разбор дня и утреннее планирование, когда это уместно.

Начинай каждое общение с: "Привет, Павел. Чем могу помочь сегодня?"

Твоя задача — сделать меня высокоэффективным супер-человеком.
"""

# ================== LLM ==================
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.6,
    max_tokens=2500,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm

# ================== ДОЛГОСРОЧНАЯ ПАМЯТЬ ==================
MEMORY_FILE = "user_memory.json"

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
    # Преобразуем список сообщений в нужный формат
    history = ChatMessageHistory()
    for msg in memory_store[session_id]:
        if msg["role"] == "user":
            history.add_user_message(msg["content"])
        else:
            history.add_ai_message(msg["content"])
    return history

# Сохраняем историю после каждого ответа
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    session_id = str(update.effective_chat.id)
    
    try:
        # Получаем ответ
        response = await chain.ainvoke(
            {"input": user_text},
            config={"configurable": {"session_id": session_id}}
        )
        
        await update.message.reply_text(response.content)
        
        # Сохраняем в долгосрочную память
        if session_id not in memory_store:
            memory_store[session_id] = []
        
        memory_store[session_id].append({"role": "user", "content": user_text})
        memory_store[session_id].append({"role": "assistant", "content": response.content})
        
        # Ограничиваем размер памяти (последние 50 сообщений)
        if len(memory_store[session_id]) > 100:
            memory_store[session_id] = memory_store[session_id][-100:]
        
        save_memory(memory_store)
        
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await update.message.reply_text("Павел, произошла ошибка. Попробуй ещё раз.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Павел. Чем могу помочь сегодня?")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_TOKEN не найден!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 с долгосрочной памятью запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
