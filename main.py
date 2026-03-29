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

# ================== ФИНАЛЬНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, стратегический партнёр и требовательный коуч 24/7.

Я выгорел от диванов, доход ≈ 100 000 ₽, уже в партнёрах UDS по тарифу "Старт". Главная цель — 300 000 ₽+ пассивного дохода в месяц через UDS.

Ты всегда начинаешь ответ с "Павел,". Только чистый русский язык.

Ты понимаешь запросы:
- "план", "составь план", "что делать дальше" — даёшь лучший план на 14 дней
- "скрипт" — генерируешь скрипт холодного звонка / сообщения
- "модель", "финансовое моделирование" — делаешь расчёт для 300к
- "воронка" — анализируешь и улучшаешь воронку продаж

Стиль:
- Требовательный, но полезный.
- Давай конкретные действия с дедлайнами.
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, Павел. Чем могу помочь сегодня?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    # Быстрые команды через текст
    if any(word in text for word in ["план", "что делать дальше", "что дальше"]):
        await update.message.reply_text("Павел, вот лучший план на 14 дней:\n\n1. Дни 1-3: Создать воронку продаж и список возражений.\n2. Дни 4-7: Провести минимум 10 холодных контактов в день.\n3. Дни 8-10: Провести презентации и переговоры.\n4. Дни 11-14: Закрыть первые сделки.\n\nС какого пункта начинаем сегодня?")
        return

    if "скрипт" in text:
        await update.message.reply_text("Павел, вот улучшенный скрипт холодного звонка:\n\n«Здравствуйте, [Имя]. Меня зовут Павел, я партнёр UDS. Мы помогаем бизнесу увеличивать доход без больших вложений. У вас есть 3 минуты, чтобы я рассказал, как наши партнёры уже зарабатывают дополнительные 50–150 тыс. в месяц?»")
        return

    if any(word in text for word in ["модель", "финансовое", "расчёт", "сколько нужно"]):
        await update.message.reply_text("Павел, финансовое моделирование:\n\nДля 300 000 ₽ пассивного дохода нужно примерно 30–40 активных партнёров (при среднем доходе 8–10 тыс. с партнёра).\nРеалистично привлечь 50 партнёров за 3–4 месяца.")
        return

    if "воронка" in text:
        await update.message.reply_text("Павел, анализ твоей воронки:\n\nСлабые места — привлечение и работа с возражениями.\nРекомендации:\n1. Сильный лид-магнит.\n2. Готовый список возражений + ответы.\n3. Этап прогрева перед звонком.\n\nХочешь полную улучшенную воронку?")
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 — максимально стабильная версия запущена — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
