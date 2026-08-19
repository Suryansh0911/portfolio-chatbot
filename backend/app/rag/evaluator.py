import json
import re
from app.services.llm import generate_response


EVALUATION_PROMPT = """
You are an evidence-based recruiter assistant.

Your task is to evaluate a candidate for a target role
using ONLY the provided portfolio evidence.

Do not invent qualifications.

Do not assume that the candidate has a skill merely because
it is common for the target role.

If a skill is not mentioned in the evidence, classify it as
"not established" rather than saying the candidate does not
have the skill.

Return ONLY valid JSON.

Do not use markdown.
Do not use ```json.
Do not add explanations outside the JSON.

Required format:

{
    "role": "ML Engineer",
    "overall_assessment": "Good potential fit",
    "matched_skills": [],
    "relevant_experience": [],
    "relevant_projects": [],
    "not_established": [],
    "reasoning": ""
}
"""


def evaluate_candidate(
    role: str,
    context: str
) -> dict:

    prompt = f"""
TARGET ROLE
===========
{role}

CANDIDATE PORTFOLIO EVIDENCE
============================
{context}

Evaluate the candidate for this role.
"""

    messages = [
        {
            "role": "system",
            "content": EVALUATION_PROMPT
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    for attempt in range(2):
        response = generate_response(
            messages,
            max_tokens=2000,
            require_json=True
        )

        print(f"\nEVALUATION RAW RESPONSE (Attempt {attempt + 1})")
        print("=" * 60)
        print(response)
        print("=" * 60)

        # Extract JSON using regex to handle any trailing tokens
        json_match = re.search(r"\{.*\}", response, flags=re.DOTALL)
        json_str = json_match.group(0) if json_match else response.strip()

        try:

            result = json.loads(
                json_str
            )

            return result

        except json.JSONDecodeError:
            
            print(f"Evaluation JSON parsing failed on attempt {attempt + 1}.")
            
            if attempt == 1: # Last attempt
                return {
                    "role": role,
                    "overall_assessment": "Unable to evaluate",
                    "matched_skills": [],
                    "relevant_experience": [],
                    "relevant_projects": [],
                    "not_established": [],
                    "reasoning": (
                        "The evaluation response could not "
                        "be parsed as valid JSON."
                    )
                }