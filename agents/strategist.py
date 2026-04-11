from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def strategist(state):
    analysis = state["analysis"]

    prompt = f"""
Ты бизнес-стратег.

Вот анализ:
{analysis}

Твоя задача:
1. НЕ повторяй анализ
2. Дай ТОЛЬКО конкретные шаги
3. Коротко и по делу

Формат:
- 5–7 действий
- без лишнего текста
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content

    return {"strategy": result}