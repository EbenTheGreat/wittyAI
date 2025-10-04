from langchain_groq import ChatGroq
from langchain_core.language_models.chat_models import BaseChatModel
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
def get_llm(model_name: str, temperature: float = 0.7) -> BaseChatModel:
    if model_name == "llama-3.1-8b-instant":
        return ChatGroq(groq_api_key=GROQ_API_KEY, model_name="llama-3.1-8b-instant", temperature=temperature)
    else:
        raise ValueError(f"Unknown model name: {model_name}")
