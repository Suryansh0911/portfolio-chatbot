import json
import os
from app.services.llm import generate_response
from groq import Groq

from app.models.schemas import Portfolio

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

RESUME_EXTRACTION_PROMPT = """You are extracting structured data from a resume into JSON.

Return ONLY a valid JSON object matching this exact schema:

{{
  "personal": {{
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "linkedin": "",
    "github": ""
  }},
  "education": [
    {{
      "degree": "",
      "institution": "",
      "location": "",
      "start_year": "",
      "end_year": ""
    }}
  ],
  "experience": [
    {{
      "company": "",
      "role": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "description": ["bullet point 1", "bullet point 2"]
    }}
  ],
  "projects": [
    {{
      "name": "",
      "description": "",
      "technologies": ["tech1", "tech2"],
      "github": ""
    }}
  ],
  "skills": ["skill1", "skill2"],
  "achievements": ["achievement1"]
}}

Rules:
- Use "" for any string field you cannot find, and [] for any missing list.
- Do not invent information that isn't in the resume text.
- "description" bullets should be concise, one point per list item.
- Output ONLY the JSON object, no markdown fences, no commentary.

Resume text:
\"\"\"
{resume_text}
\"\"\"
"""


def resume_text_to_portfolio(raw_text: str) -> Portfolio:
    """
    Sends raw extracted resume text to Groq, gets back structured JSON,
    and validates it against the Portfolio schema.
    """

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "user",
                "content": RESUME_EXTRACTION_PROMPT.format(resume_text=raw_text),
            }
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Groq returned invalid JSON: {e}\nRaw output: {content}")

    try:
        portfolio = Portfolio(**data)
    except Exception as e:
        raise ValueError(f"Groq output didn't match Portfolio schema: {e}\nData: {data}")

    return portfolio