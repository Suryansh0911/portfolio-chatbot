from app.services.llm import generate_response
import re

FOLLOW_UP_TERMS = {
    "he",
    "his",
    "him",
    "there",
    "this",
    "that",
    "it",
    "one",
    "they",
    "them",
    "these",
    "those",
}


def needs_query_rewrite(
    user_message: str,
    history: list[dict]) -> bool:

    if not history:
        return False

    words = {
        word.strip(".,?!'\"").lower()
        for word in user_message.split()
    }

    return bool(
        words.intersection(FOLLOW_UP_TERMS)
    )

QUERY_REWRITE_PROMPT = """
You are the query rewriting component of a professional
portfolio chatbot for Suryansh Gupta.

Your ONLY task is to rewrite the recruiter's latest question
into ONE standalone search query for portfolio retrieval.

You must NOT answer the question.

The search query will be passed to a hybrid retriever using
semantic search, BM25, metadata filtering, and reranking.

CONVERSATION RESOLUTION RULES
=============================

1. Use the conversation history to resolve references such as:
   - he
   - his
   - him
   - there
   - this
   - that
   - it
   - they
   - them
   - this project
   - that project
   - this company
   - that company
   - there

2. Resolve references using the MOST RECENT relevant topic
   in the conversation.

3. Preserve explicit entities from the latest question.

4. If the latest question contains a pronoun or vague reference,
   replace it with the specific entity from the conversation.

5. Never replace a specific entity with a vague reference.

ENTITY PRESERVATION
===================

Preserve important portfolio entities exactly.

Examples:

SmartED
→ SmartED Innovations

Suryansh
→ Suryansh Gupta

SVNIT
→ Sardar Vallabhbhai National Institute of Technology (SVNIT)

QUERY TYPE
==========

For employment or internship questions, include relevant terms
such as:

work, role, internship, experience, company

For project questions, include:

project, technologies, implementation, description

For technology questions, include:

technologies, tech stack, tools, frameworks

For education questions, include:

degree, education, institution, university, coursework

For achievements, include:

achievement, result, impact, performance

IMPORTANT RULES
===============

- Return ONLY the rewritten search query.
- Do not answer the question.
- Do not explain the rewrite.
- Do not invent facts.
- Do not introduce technologies, companies, projects, roles,
  or experiences that are not present in the conversation.
- Keep the query concise but information-rich.
- Make the query standalone so it can be understood without
  the conversation history.

EXAMPLES
========

History:
Recruiter: What did Suryansh do at SmartED?

Latest:
What tech stack did he use there?

Output:
Suryansh Gupta technologies and tech stack used during his
work experience at SmartED Innovations

---

History:
Recruiter: What NLP projects has Suryansh built?

Latest:
Which one uses FAISS?

Output:
Suryansh Gupta NLP project using FAISS

---

History:
Recruiter: Tell me about the Local AI Companion.

Latest:
What technologies did he use in it?

Output:
Suryansh Gupta Local AI Companion technologies and tech stack

---

History:
Recruiter: What did Suryansh do at SmartED?

Latest:
What did he study at SVNIT?

Output:
Suryansh Gupta education degree coursework at SVNIT

---

History:
Recruiter: Tell me about SmartED.

Latest:
Has he worked at Google?

Output:
Suryansh Gupta work experience at Google
"""

def rewrite_query(
    user_message: str,
    history: list[dict]) -> str:

    conversation_parts = []

    for message in history:

        role = message.get("role", "")
        content = message.get("content", "")

        if not content:
            continue

        conversation_parts.append(
            f"{role.upper()}: {content}"
        )

    conversation = "\n".join(conversation_parts)

    prompt = f"""
    CONVERSATION HISTORY
    ====================

    {conversation}

    LATEST RECRUITER QUESTION
    =========================

    {user_message}

    Rewrite the latest question into a standalone
    search query.
    """

    messages = [
        {
            "role": "system",
            "content": QUERY_REWRITE_PROMPT
        },
        {
            "role": "user",
            "content": prompt
        }
    ]

    rewritten_query = generate_response(
        messages).strip()

    rewritten_query = re.sub(
        r"<think>.*?</think>", "",
        rewritten_query, flags=re.DOTALL | re.IGNORECASE    
    ).strip()

    rewritten_query = re.sub(
        r"^'''(?:text)?\s*", "",
        rewritten_query, flags=re.IGNORECASE
    )
    rewritten_query = re.sub(
    r"\s*```$",
    "",
    rewritten_query
    ).strip()

    return rewritten_query