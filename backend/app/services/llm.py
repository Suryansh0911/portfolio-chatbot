from collections.abc import Iterator
from groq import Groq
from app.core.config import GROQ_API_KEY


client = Groq(
    api_key=GROQ_API_KEY
)

model = "openai/gpt-oss-20b"


def generate_response(
    messages: list[dict],
    max_tokens: int = 1024,
    require_json: bool = False
) -> str:
    
    kwargs = {
        "model": model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": max_tokens,
        "reasoning_effort": "medium",
        "reasoning_format": "hidden"
    }
    
    if require_json:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)

    return response.choices[0].message.content


def generate_response_stream(
    messages: list[dict]
) -> Iterator[str]:

    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
        reasoning_effort="medium",
        reasoning_format="hidden",
        stream=True
    )

    for chunk in stream:

        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta

        if not delta:
            continue

        content = delta.content

        if content:
            yield content