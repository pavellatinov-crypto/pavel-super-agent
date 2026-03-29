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

# ================== ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и требовательный коуч 24/7.

Я выгорел от диванов, доход ≈ 100 000 ₽, уже в партнёрах UDS по тарифу "Старт". Главная цель — 300 000 ₽+ пассивного дохода в месяц через UDS.

Ты всегда начинаешь ответ с "Павел,". Только чистый русский язык.

Ты умеешь работать с командами:
- /plan — лучший план на 14 дней
- /script — скрипт холодного звонка / сообщения
- /model — финансовое моделирование
- /воронка — анализ и улучшение воронки продаж

Стиль:
- Требовательный, но полезный.
- Если я использую команду — сразу даёшь готовый результат.
- Если обычное сообщение — отвечай по делу с конкретными шагами.
- Фокус всегда на UDS и уходе от диванов.
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

# ================== КОМАНДЫ ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Павел. Чем могу помочь сегодня?")

async def plan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Павел, вот лучший план на 14 дней:\n\n1. Дни 1-3: Создать воронку продаж и список возражений.\n2. Дни 4-7: Провести минимум 10 холодных контактов в день.\n3. Дни 8-10: Провести презентации и переговоры.\n4. Дни 11-14: Закрыть первые сделки и проанализировать результаты.\n\nС какого пункта начинаем сегодня?")

async def script_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Павел, вот улучшенный скрипт холодного звонка:\n\n«Здравствуйте, [Имя]. Меня зовут Павел, я партнёр UDS. Мы помогаем бизнесу увеличивать доход без больших вложений. У вас есть 3 минуты, чтобы я рассказал, как наши партнёры уже зарабатывают дополнительные 50–150 тыс. в месяц?»")

async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Павел, финансовое моделирование:\n\nДля 300 000 ₽ пассивного дохода в месяц нужно примерно 30–40 активных партнёров (при среднем доходе 8–10 тыс. с партнёра).\nРеалистично: привлечь 50 партнёров за 3–4 месяца с учётом оттока.\n\nХочешь расчёт под твои текущие данные?")

async def voronka_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Павел, анализ твоей воронки:\n\nСлабые места — привлечение и работа с возражениями.\n\nРекомендации:\n1. Сильный лид-магнит (бесплатная консультация или мини-книга).\n2. Готовый список возражений + ответы.\n3. Этап прогрева перед звонком.\n\nХочешь полную улучшенную воронку с этапами?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip().lower()

    if user_text == "/plan":
        await plan_command(update, context)
        return
    elif user_text == "/script":
        await script_command(update, context)
        return
    elif user_text == "/model":
        await model_command(update, context)
        return
    elif user_text in ["/воронка", "/voronka"]:
        await voronka_command(update, context)
        return

    # Обычное сообщение
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
    app.add_handler(CommandHandler("plan", plan_command))
    app.add_handler(CommandHandler("script", script_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("воронка", voronka_command))
    app.add_handler(CommandHandler("voronka", voronka_command))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 с быстрыми командами запущен — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
