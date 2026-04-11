from graph import graph

state = {
    "user_input": "Салон красоты, мало клиентов",
    "analysis": "",
    "strategy": "",
    "content": "",
    "goal": "выйти на 300000 рублей в месяц через UDS"
}

result = graph.invoke(state)

print("\n=== АНАЛИЗ ===\n")
print(result["analysis"])

print("\n=== СТРАТЕГИЯ ===\n")
print(result["strategy"])

print("\n=== КОНТЕНТ ===\n")
print(result["content"])