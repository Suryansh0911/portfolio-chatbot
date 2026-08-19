import json
import re

from app.services.llm import generate_response


MAX_SUBQUESTIONS = 5


DECOMPOSER_PROMPT = """
You decompose recruiter questions about Suryansh Gupta's portfolio
into independent questions that can be answered separately.

Rules:

1. Extract every distinct answerable request.
2. Return at most 5 questions.
3. Do not split one logical request into artificial fragments.
4. Preserve important entities exactly.
5. Preserve resolved names such as Suryansh Gupta.
6. Each sub-question must be standalone.
7. Do not answer the questions.
8. Return ONLY valid JSON.
9. Do not include <think> blocks.

Examples:

Input:
Where has Suryansh used Hugging Face and LangChain?

Output:
{
    "questions": [
        "Where has Suryansh used Hugging Face?",
        "Where has Suryansh used LangChain?"
    ]
}

Input:
Is he a good fit for a Machine Learning Engineer role, and what is his email address?

Output:
{
    "questions": [
        "Is Suryansh a good fit for a Machine Learning Engineer role?",
        "What is Suryansh's email address?"
    ]
}

Input:
What degree does Suryansh have, where did he study,
and what was his CGPA?

Output:
{
    "questions": [
        "What degree does Suryansh have?",
        "Where did Suryansh study?",
        "What was Suryansh's CGPA?"
    ]
}

Input:
What technologies did Suryansh use in his projects?

Output:
{
    "questions": [
        "What technologies did Suryansh use in his projects?"
    ]
}
"""


def _clean_response(response: str) -> str:
    json_match = re.search(r"\{.*\}", response, flags=re.DOTALL)
    if json_match:
        return json_match.group(0)
    return response.strip()


def is_likely_compound(question: str) -> bool:

    text = question.lower()

    markers = (
        " and ",
        " or ",
        " as well as ",
        " along with ",
        " also ",
        ", and ",
        ", or ",
    )

    return any(
        marker in text
        for marker in markers
    )


def decompose_question(
    question: str
) -> list[str]:

    if not is_likely_compound(question):
        return [question]

    messages = [
        {
            "role": "system",
            "content": DECOMPOSER_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ]

    response = generate_response(
        messages
    )

    print("\nQUESTION DECOMPOSER RAW RESPONSE")
    print("=" * 60)
    print(response)
    print("=" * 60)

    cleaned = _clean_response(response)

    try:

        data = json.loads(cleaned)

        questions = data.get(
            "questions",
            []
        )

        if not isinstance(
            questions,
            list
        ):
            return [question]

        cleaned_questions = [
            str(item).strip()
            for item in questions
            if str(item).strip()
        ]

        if not cleaned_questions:
            return [question]

        return cleaned_questions[
            :MAX_SUBQUESTIONS
        ]

    except (
        json.JSONDecodeError,
        TypeError,
        ValueError
    ) as e:

        print(
            f"Question decomposition failed: {e}"
        )

        return [question]