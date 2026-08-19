import json
import re

from app.services.llm import generate_response


VERIFIER_PROMPT = """
You are an evidence verification system for a professional
portfolio chatbot.

Your job is to determine whether the retrieved portfolio
information actually contains evidence needed to answer
the user's question.

Do not judge whether the documents are merely related to
the candidate.

Judge whether they support the specific claim in the question.

Return ONLY valid JSON:

{
    "supported": true,
    "reason": "brief explanation"
}

or

{
    "supported": false,
    "reason": "brief explanation"
}

Rules:
- Do not infer facts that are not present.
- Do not use general world knowledge.
- Absence of evidence should result in supported=false.
- If the portfolio explicitly supports the answer, use supported=true.
- Do not use Markdown code fences.
- Do not include <think> or any reasoning in the final response.
"""


def clean_response(response: str) -> str:
    """Remove model reasoning and Markdown formatting."""

    response = response.strip()

    # Remove <think>...</think>
    response = re.sub(
        r"<think>.*?</think>",
        "",
        response,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Remove ```json ... ``` or ``` ... ```
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


def verify_evidence(
    question: str,
    context: str
) -> dict:

    prompt = f"""
USER QUESTION
=============

{question}

RETRIEVED PORTFOLIO INFORMATION
================================

{context}
"""

    messages = [
        {
            "role": "system",
            "content": VERIFIER_PROMPT
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = generate_response(
        messages
    )

    print("\nEVIDENCE VERIFIER RAW RESPONSE")
    print("=" * 60)
    print(response)
    print("=" * 60)

    cleaned = clean_response(response)

    try:

        result = json.loads(cleaned)

        supported = result.get(
            "supported",
            False
        )

        if not isinstance(supported, bool):
            return {
                "supported": False,
                "reason": "Invalid evidence verification result."
            }

        return {
            "supported": supported,
            "reason": str(
                result.get(
                    "reason",
                    ""
                )
            )
        }

    except json.JSONDecodeError as e:

        print(
            f"Evidence verification JSON parsing failed: {e}"
        )

        return {
            "supported": False,
            "reason": "Evidence verification failed."
        }