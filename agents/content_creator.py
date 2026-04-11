from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def content_creator(state):
    strategy = state["strategy"]

    prompt = f"""
Ты маркетолог.

Вот стратегия:
{strategy}

Сделай:
1. 3 коротких продающих сообщения
2. Без повторения стратегии
3. Готово к отправке клиенту

Формат:
- Сообщение 1
- Сообщение 2
- Сообщение 3
"""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    result = response.choices[0].message.content

    return {"content": result}