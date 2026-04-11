from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def controller(state):
    analysis = state["analysis"]
    strategy = state["strategy"]
    content = state["content"]

    prompt = f"""
Ты опытный бизнес-консультант.

Проверь работу команды:

АНАЛИЗ:
{analysis}

СТРАТЕГИЯ:
{strategy}

КОНТЕНТ:
{content}

Твоя задача:
1. Найди слабые места
2. Улучши стратегию
3. Улучши тексты (сделай более продающими)

Верни финальную версию:
- Финальная стратегия
- Финальные тексты
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content

    return {"content": result}