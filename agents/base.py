import os

from agno.models.openai import OpenAIChat


def get_model(temperature: float = 0.4):
    model_id = os.getenv("OPENAI_MODEL_ID", "gpt-4.1")
    token_kwargs = {"max_completion_tokens": 4096} if model_id.startswith("gpt-5") else {"max_tokens": 4096}
    return OpenAIChat(
        id=model_id,
        temperature=temperature,
        **token_kwargs,
    )
