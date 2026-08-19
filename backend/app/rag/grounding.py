import json
import re

from app.services.llm import generate_response


GROUNDING_PROMPT = """
You are a strict fact-checker for a professional portfolio chatbot.

You will receive:

1. The recruiter's question
2. The generated answer
3. The portfolio evidence used to generate the answer

Your job is to determine whether the generated answer is supported
by the portfolio evidence.

Rules:

- SUPPORTED:
  The answer is directly supported by the portfolio evidence.

- PARTIALLY_SUPPORTED:
  Some claims are supported, but some claims go beyond the evidence.

- UNSUPPORTED:
  The answer contains important claims that are not supported by
  the evidence.

Do not use outside knowledge.

Important:

- For questions asking whether Suryansh has worked at, used, built,
  or experienced something, do not treat unrelated portfolio
  information as evidence that the answer is "no".
- If the retrieved evidence does not explicitly establish the
  requested fact, return UNSUPPORTED.
- Do not infer facts from the absence of information.
- Do not invent qualifications, employers, technologies,
  responsibilities, projects, or achievements.

Return ONLY valid JSON.
Do not use Markdown code fences.
Do not include <think> blocks in your final response.

Required format:

{
    "verdict": "SUPPORTED",
    "reason": "Short explanation"
}

The verdict must be exactly one of:

SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED
"""


def clean_response(response: str) -> str:
    """
    Clean common LLM formatting artifacts before JSON parsing.

    Handles:
    - <think>...</think>
    - ```json ... ```
    - ``` ... ```
    - surrounding whitespace
    """

    cleaned = response.strip()

    # Remove exposed reasoning blocks.
    cleaned = re.sub(
        r"<think>.*?</think>",
        "",
        cleaned,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Remove opening Markdown code fence.
    cleaned = re.sub(
        r"^```(?:json|text)?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE
    )

    # Remove closing Markdown code fence.
    cleaned = re.sub(
        r"\s*```$",
        "",
        cleaned
    )

    return cleaned.strip()


def parse_grounding_response(
    response: str
) -> dict:
    """
    Parse and validate the grounding verifier's JSON response.
    """

    cleaned = clean_response(response)

    try:
        result = json.loads(cleaned)

    except json.JSONDecodeError as e:

        print(
            f"Grounding JSON parsing failed: {e}"
        )

        return {
            "verdict": "UNSUPPORTED",
            "reason": "Grounding verification failed."
        }

    if not isinstance(result, dict):
        return {
            "verdict": "UNSUPPORTED",
            "reason": "Invalid grounding response format."
        }

    verdict = str(
        result.get(
            "verdict",
            "UNSUPPORTED"
        )
    ).upper().strip()

    reason = str(
        result.get(
            "reason",
            ""
        )
    ).strip()

    valid_verdicts = {
        "SUPPORTED",
        "PARTIALLY_SUPPORTED",
        "UNSUPPORTED"
    }

    if verdict not in valid_verdicts:
        return {
            "verdict": "UNSUPPORTED",
            "reason": "Invalid grounding verdict returned."
        }

    return {
        "verdict": verdict,
        "reason": reason
    }


def check_grounding(
    question: str,
    answer: str,
    context: str
) -> dict:

    prompt = f"""
RECRUITER QUESTION
==================
{question}

GENERATED ANSWER
================
{answer}

PORTFOLIO EVIDENCE
==================
{context}
"""

    messages = [
        {
            "role": "system",
            "content": GROUNDING_PROMPT
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    response = generate_response(
        messages
    )

    print("\nGROUNDING RAW RESPONSE")
    print("=" * 60)
    print(response)
    print("=" * 60)

    result = parse_grounding_response(
        response
    )

    print(
        f"Grounding Verdict: "
        f"{result['verdict']}"
    )

    print(
        f"Grounding Reason: "
        f"{result['reason']}"
    )

    return result