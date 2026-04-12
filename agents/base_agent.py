from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from config import Config

class BaseAgent(ABC):
    """Это базовый робот, от которого будут наследоваться все остальные роботы"""
    
    def __init__(self, name: str):
        self.name = name
        self.llm = ChatOpenAI(
            model=Config.LLM_MODEL,
            temperature=Config.TEMPERATURE,
            max_tokens=Config.MAX_TOKENS,
            openai_api_key=Config.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
        )

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Здесь каждый робот будет описывать, кто он и что умеет"""
        pass

    async def invoke(self, query: str, state: dict) -> str:
        """Этот метод вызывает робота и просит его ответить"""
        full_prompt = self.get_system_prompt() + f"\n\nТекущая ситуация: {state.get('context', {})}"
        
        response = await self.llm.ainvoke([
            ("system", full_prompt),
            ("human", query)
        ])
        return response.content
