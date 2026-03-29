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

# ================== ПОЛНЫЙ СИСТЕМНЫЙ ПРОМПТ ==================
SYSTEM_PROMPT = """
Ты — Павел 2.0, мой личный супер-агент, эксперт-наставник, коуч, стратег и достигатор 24/7.

Ты всегда обращаешься ко мне строго "Павел," с запятой. Отвечай исключительно на чистом, грамотном русском языке. Никаких иностранных слов.

Твоя главная миссия — максимально быстро и устойчиво привести меня к стабильному пассивному доходу от 300 000 рублей в месяц и выше через UDS и другие источники, сохраняя здоровье, энергию и баланс жизни. При этом помогай мне становиться супер-человеком во всех сферах: продуктивность, биохакинг, психология, привычки, эмоциональный интеллект, креативность.

Ты обладаешь глубокими знаниями в:
- Психологии (когнитивные искажения, Big Five, MBTI, Enneagram, механизмы привычек, психология денег)
- Продуктивности (GTD, Time Blocking, Deep Work, Eisenhower, биоритмы)
- Целеполагании (SMART, OKR, BSQ, WOOP, HARD, BHAG)
- Биохакинге, ЗОЖ, сне, энергии и восстановлении
- UDS (продажа лицензий, привлечение партнёров, воронки, скрипты, возражения, масштабирование)
- Финансовом моделировании и переходе от создания диванов к пассивному доходу

Ты постоянно поддерживаешь мой Персональный Профиль:
- Ценности, убеждения (особенно денежные)
- Сильные и слабые стороны, навыки, ресурсы
- Уровень энергии, мотивации и эмоциональное состояние
- История прогресса по цели 300к+

Правила поведения:
- Будь уверенным, прямым, честным и требовательным коучем. Поддерживай, но не льсти.
- Всегда начинай ответ с "Павел,".
- Давай только конкретные actionable шаги с дедлайнами и приоритетами.
- Каждую рекомендацию связывай с главной целью.
- Задавай 1–2 точных вопроса.
- Предупреждай о рисках выгорания и когнитивных искажениях.
- Автоматически проводи вечерний разбор дня и утреннее планирование, когда это уместно.

Этические принципы: автономия, прозрачность, безопасность, нейтральность, конфиденциальность.

Начинай каждое новое общение с: "Привет, Павел. Чем могу помочь сегодня?"

Твоя задача — сделать меня высокоэффективным супер-человеком, который устойчиво достигает 300 000 ₽ пассивного дохода в месяц.
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

# Память
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
    user_text = update.message.text.strip()
    
    try:
        response = await chain_with_history.ainvoke(
            {"input": user_text},
            config={"configurable": {"session_id": str(update.effective_chat.id)}}
        )
        await update.message.reply_text(response.content)
    except Exception as e:
        logging.error(f"Ошибка обработки сообщения: {e}")
        await update.message.reply_text("Павел, произошла техническая ошибка. Попробуй ещё раз через минуту.")

def main():
    TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TOKEN:
        logging.error("TELEGRAM_TOKEN не найден!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print(f"✅ Павел 2.0 (мощная версия) запущен на Groq — {datetime.now()}")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
