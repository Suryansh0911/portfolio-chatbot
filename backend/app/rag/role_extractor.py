import json
import re
from app.services.llm import generate_response



ROLE_EXTRACTION_PROMPT = """
You extract job roles from recruiter questions about Suryansh Gupta.

Your task is to identify every distinct job role that the recruiter
is asking you to evaluate.

Rules:

1. Extract ALL roles mentioned in the question.
2. Preserve the meaning of the role.
3. Normalize obvious variations where appropriate.
4. If the question refers to a general CATEGORY of roles rather than
   a specific title (e.g. "data related roles", "AI roles", "tech
   roles"), expand it into the 2-3 most representative concrete job
   titles for that category. Do not return an empty list just
   because no exact title was named.

Examples:

"Is Suryansh a good fit for a data science or an AI engineer role?"
→
{
    "roles": [
        "Data Scientist",
        "AI Engineer"
    ]
}

"Would he be suitable for ML Engineer?"
→
{
    "roles": [
        "ML Engineer"
    ]
}

"How does he compare for Data Scientist, NLP Engineer, and
AI Engineer positions?"
→
{
    "roles": [
        "Data Scientist",
        "NLP Engineer",
        "AI Engineer"
    ]
}

"Is he a good fit for data related roles?"
→
{
    "roles": [
        "Data Scientist",
        "Data Analyst",
        "ML Engineer"
    ]
}

"Is he a good fit for AI roles?"
→
{
    "roles": [
        "AI Engineer",
        "ML Engineer"
    ]
}

"Is his profile suitable for this role?"
→
{
    "roles": []
}

Return ONLY valid JSON.

Do not use Markdown.
Do not include <think> blocks.

Required format:

{
    "roles": [
        "Data Scientist",
        "AI Engineer"
    ]
}
"""


def _clean_response(
    response: str
) -> str:

    response = response.strip()

    # Remove exposed reasoning
    response = re.sub(
        r"<think>.*?</think>",
        "",
        response,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Remove Markdown fences
    response = re.sub(
        r"^```(?:json)?\s*",
        "",
        response,
        flags=re.IGNORECASE
    )

    response = re.sub(
        r"\s*```$",
        "",
        response
    ).strip()

    return response


def extract_roles(
    user_message: str
) -> list[str]:

    messages = [
        {
            "role": "system",
            "content": ROLE_EXTRACTION_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = generate_response(
        messages
    )

    print("\nROLE EXTRACTION RAW RESPONSE")
    print("=" * 60)
    print(response)
    print("=" * 60)

    cleaned = _clean_response(
        response
    )

    try:

        data = json.loads(
            cleaned
        )

        roles = data.get(
            "roles",
            []
        )

        if not isinstance(
            roles,
            list
        ):
            return []

        return [
            str(role).strip()
            for role in roles
            if str(role).strip()
        ]

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError
    ) as e:

        print(
            f"Role extraction failed: {e}"
        )

        return []