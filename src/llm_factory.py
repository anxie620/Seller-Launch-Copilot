import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from typing import Optional

# Default to OpenAI
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

def get_llm(temperature: float = 0, model_name: Optional[str] = None):
    """
    Returns a configured ChatOpenAI instance.
    Uses environment variables for configuration.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL)
    model = model_name or os.getenv("OPENAI_MODEL_NAME", DEFAULT_MODEL)

    if not api_key:
        return None

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        openai_api_key=api_key,
        openai_api_base=base_url
    )

def get_embeddings():
    """
    Returns a configured OpenAIEmbeddings instance.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL)
    # Alibaba Cloud Qwen compatible embeddings usually use text-embedding-v1 or similar
    # But if using standard OpenAI, it's text-embedding-3-small
    # We will allow env var override
    model = os.getenv("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)

    if not api_key:
        return None

    return OpenAIEmbeddings(
        model=model,
        openai_api_key=api_key,
        openai_api_base=base_url
    )
