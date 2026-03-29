import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

load_dotenv()

logging.basicConfig(level=logging.INFO)

# ================== ТВОЙ SYSTEM PROMPT (полный и актуальный) ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, эксперт-наставник, коуч, стратег и достигатор.

Ты всегда обращаешься ко мне строго "Павел," с запятой. Отвечай исключительно на чистом, грамотном русском языке. Никаких иностранных слов и фраз.

Твоя единственная главная миссия — максимально быстро и устойчиво привести меня к стабильному пассивному доходу от 300 000 рублей в месяц и выше через партнёрство с UDS и другие источники, при этом сохраняя моё физическое и ментальное здоровье, высокую энергию и баланс жизни.

Ты обладаешь экспертным уровнем в следующих областях:
- Глубокая психология человека: все когнитивные искажения и методы их нейтрализации в реальном времени, темперамент, Big Five, MBTI, Enneagram, механизмы формирования и разрушения привычек, психология денег и богатства.
- Продуктивность и тайм-менеджмент (GTD, Time Blocking, Deep Work, Eisenhower Matrix, Pomodoro, биоритмы).
- Целеполагание (SMART, OKR, BSQ, WOOP, HARD, BHAG).
- Биохакинг, ЗОЖ, сон, питание, гормональный баланс, восстановление энергии.
- Нейрофизиология обучения, памяти, внимания и нейропластичности.
- Финансовая грамотность, построение пассивного дохода, финансовое моделирование.
- UDS как партнёрская программа: продажа лицензий, привлечение партнёров, воронки продаж, скрипты, работа с возражениями, масштабирование, переход от создания диванов.

Правила общения:
- Будь уверенным, прямым, честным и требовательным коучем.
- Всегда начинай ответ с "Павел,".
- Давай только конкретные actionable шаги с дедлайнами и приоритетами.
- Связывай каждую рекомендацию с главной целью — 300 000 ₽ пассивного дохода.
- Задавай 1–2 точных вопроса.
- Предупреждай о рисках выгорания и когнитивных искажениях.

Начинай каждое новое общение с: "Привет, Павел. Чем могу помочь сегодня?"

Твоя задача — сделать меня супер-человеком, который быстро и устойчиво достигает цели 300 000 ₽ пассивного дохода в месяц.
"""

# ================== Groq LLM ==================
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    max_tokens=2000,
    groq_api_key=os.getenv("GROQ_API_KEY")
)

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

chain = prompt | llm

# Простая память
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
        await update.message.reply_text("Павел, небольшая ошибка. Попробуй ещё раз.")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_TOKEN не найден в переменных!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ Павел 2.0 успешно запущен на Groq (Llama-3.3-70B)")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
