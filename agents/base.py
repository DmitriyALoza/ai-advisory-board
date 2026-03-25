import os

from agno.models.openai import OpenAIChat


def get_model(temperature: float = 0.4):
    model_id = os.getenv("OPENAI_MODEL_ID", "gpt-4.1")
    return OpenAIChat(
        id=model_id,
        temperature=temperature,
        max_tokens=4096,
    )
