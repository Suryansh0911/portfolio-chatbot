from enum import Enum
import json
import re

from app.services.llm import generate_response


class Intent(str, Enum):

    FACTUAL = "factual"
    PROJECT = "project"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    CERTIFICATION = "certification"
    ACHIEVEMENT = "achievement"
    SUMMARY = "summary"
    EVALUATION = "evaluation"
    PERSONAL = "personal"
    UNKNOWN = "unknown"


INTENT_PROMPT = """
You are an intent classifier for Suryansh Gupta's professional
portfolio chatbot.

Classify the user's question into exactly ONE of these intents:

- factual
  General factual questions about Suryansh.

- education
  Questions about degrees, education, university, institution,
  graduation, CGPA, coursework, or academic background.

- experience
  Questions about internships, jobs, companies, roles,
  responsibilities, or professional work experience.

- project
  Questions about projects Suryansh has built or developed.

- skills
  Questions about technical skills, technologies, frameworks,
  tools, programming languages, or tech stack.

- certification
  Questions about certifications.

- achievement
  Questions about achievements, measurable results,
  accomplishments, or awards.

- personal
  Questions specifically asking for personal/contact/profile
  information available in the portfolio.

- summary
  Questions asking for a general summary, overview of his profile,
  his greatest strengths, weaknesses, general fit, or broad pitches
  like "why should I hire Suryansh?", "tell me about him", or 
  "what makes him a good candidate?".

- evaluation
  Questions asking whether Suryansh is suitable for a SPECIFIC role,
  job title, or position (e.g., "Is he a good fit for a Data Scientist role?",
  "Can he work as a backend engineer?"). If no specific role is mentioned,
  use 'summary' instead.

- unknown
  Use this only when the question is unrelated to Suryansh's
  portfolio or cannot reasonably be classified.

Return ONLY valid JSON:

{
    "intent": "education"
}

Do not explain your answer.
"""


def _clean_response(response: str) -> str:

    response = response.strip()

    # Remove exposed reasoning
    response = re.sub(
        r"<think>.*?</think>",
        "",
        response,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Remove markdown fences
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


def classify_intent(
    user_message: str
) -> Intent:

    messages = [
        {
            "role": "system",
            "content": INTENT_PROMPT
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    response = generate_response(messages)

    print("\nINTENT RAW RESPONSE")
    print("=" * 60)
    print(response)
    print("=" * 60)

    cleaned = _clean_response(response)

    try:
        data = json.loads(cleaned)

        intent_value = str(
            data.get("intent", "unknown")
        ).strip().lower()

        return Intent(intent_value)

    except (json.JSONDecodeError, ValueError, TypeError) as e:

        print(
            f"Intent parsing failed: {e}"
        )

        # Fallback if model returned just:
        # education
        candidate = cleaned.strip().lower()

        try:
            return Intent(candidate)
        except ValueError:
            return Intent.UNKNOWN