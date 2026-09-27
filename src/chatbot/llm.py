"""LLM provider factory: Groq (free tier) | OpenAI | Ollama (local)."""
from src import config


def get_llm():
    provider = config.LLM_PROVIDER
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(model=config.GROQ_MODEL, temperature=0)
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=config.OPENAI_MODEL, temperature=0)
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(model=config.OLLAMA_MODEL, temperature=0)
    raise ValueError(
        f"Unknown MEDASSIST_LLM_PROVIDER={provider!r}. Use groq | openai | ollama."
    )
