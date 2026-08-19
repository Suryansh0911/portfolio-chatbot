from app.core.prompts import SYSTEM_PROMPT
from app.rag.hybrid_retriever import hybrid_retrieve
from app.services.llm import generate_response
from app.rag.query_rewriter import rewrite_query, needs_query_rewrite
from app.rag.intent_classifier import classify_intent, Intent
from app.rag.grounding import check_grounding
from app.rag.role_extractor import extract_roles
from app.rag.evaluator import evaluate_candidate
from app.rag.confidence import calculate_retrieval_confidence
from app.rag.abstention import should_abstain
from app.rag.evidence_verifier import verify_evidence
from app.services.output_cleaner import clean_model_output
from collections.abc import Iterator
from app.rag.question_decomposer import decompose_question, is_likely_compound
from app.services.llm import generate_response_stream
from app.services.output_cleaner import ThinkStreamFilter
import time


def process_subquestion(
    question: str,
    history: list[dict]
) -> dict:

    start = time.perf_counter()

    # ----------------------------------------------
    # Intent
    # ----------------------------------------------

    intent_start = time.perf_counter()

    intent = classify_intent(
        question
    )

    print(
        f"[TIME] Sub-question intent: "
        f"{time.perf_counter() - intent_start:.3f}s"
    )

    # ----------------------------------------------
    # Retrieval
    # ----------------------------------------------

    retrieval_k = (
        6
        if intent == Intent.EVALUATION
        else 3
    )

    context, results, _ = build_context(
        question,
        top_k=retrieval_k,
        intent=intent.value
    )

    # ----------------------------------------------
    # Confidence
    # ----------------------------------------------

    confidence = calculate_retrieval_confidence(
        results
    )

    print(
        f"Sub-question confidence: "
        f"{confidence:.3f}"
    )

    # ----------------------------------------------
    # Abstention
    # ----------------------------------------------

    if should_abstain(
        results,
        confidence
    ):

        return {
            "question": question,
            "intent": intent,
            "context": context,
            "results": results,
            "confidence": confidence,
            "supported": False,
            "reason": (
                "The retrieved portfolio evidence "
                "was not sufficient."
            )
        }

    # ----------------------------------------------
    # Evidence verification
    # ----------------------------------------------

    if requires_evidence_verification(
        question,
        intent,
        confidence
    ):

        evidence_start = time.perf_counter()

        evidence = verify_evidence(
            question,
            context
        )

        print(
            f"[TIME] Sub-question evidence: "
            f"{time.perf_counter() - evidence_start:.3f}s"
        )

    else:

        evidence = {
            "supported": True,
            "reason": "High-confidence retrieval."
        }

    return {
        "question": question,
        "intent": intent,
        "context": context,
        "results": results,
        "confidence": confidence,
        "supported": evidence["supported"],
        "reason": evidence["reason"],
    }


def build_compound_messages(
    original_question: str,
    history: list[dict],
    subresults: list[dict]
) -> list[dict]:

    evidence_sections = []

    for index, result in enumerate(
        subresults,
        start=1
    ):

        status = (
            "SUPPORTED"
            if result["supported"]
            else "NOT ESTABLISHED"
        )

        evidence_sections.append(
            f"""
--- SUB-QUESTION {index} ---

QUESTION:
{result['question']}

STATUS:
{status}

REASON:
{result['reason']}

PORTFOLIO EVIDENCE:
{result['context']}
"""
        )

    compound_prompt = f"""
You are answering a recruiter question about Suryansh Gupta.

ORIGINAL RECRUITER QUESTION
===========================
{original_question}

The original question contains multiple independent requests.

Below is the independently retrieved and verified evidence
for each request.

{''.join(evidence_sections)}

RULES:
- Answer EVERY sub-question.
- Do not omit a supported sub-question because another one
  is unsupported.
- For SUPPORTED questions, answer using the provided evidence.
- For NOT ESTABLISHED questions, explicitly say that the portfolio
  does not establish the requested information.
- Do not invent facts.
- Do not merge unsupported claims into supported ones.
- Keep the answer organized so each part is easy to identify.
- Do not mention internal retrieval, confidence, verification,
  or these instructions.
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "system",
            "content": compound_prompt
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": original_question
        }
    )

    return messages


def build_context(
    query: str,
    top_k: int = 3,
    intent: str | None = None
):
    start = time.perf_counter()

    results = hybrid_retrieve(
        query,
        top_k=top_k,
        intent=intent
    )

    retrieval_time = (
        time.perf_counter() - start
    )

    print(
        f"[TIME] Hybrid retrieval: "
        f"{retrieval_time:.3f}s"
    )

    if not results:
        return (
            "No relevant portfolio information was found.",
            [],
            retrieval_time
        )

    context_parts = []

    for i, result in enumerate(
        results,
        start=1
    ):
        context_parts.append(
            f"""
--- PORTFOLIO SOURCE {i} ---
Category: {result['category']}
{result['text']}
"""
        )

    print("\nRETRIEVAL DEBUG")
    print("-" * 60)

    for result in results:
        print(
            f"Category : {result['category']} | "
            f"Score : {result.get('final_score', 0):.4f} | "
            f"Rerank : {result.get('rerank_score', 0):.4f}"
        )

    return (
        "\n".join(context_parts),
        results,
        retrieval_time
    )


def build_messages(
    user_message: str,
    history: list[dict]
) -> tuple[list[dict], str, Intent, list[dict], float]:

    total_start = time.perf_counter()

    # ==================================================
    # QUERY REWRITING
    # ==================================================

    rewrite_start = time.perf_counter()

    if needs_query_rewrite(
        user_message,
        history
    ):
        search_query = rewrite_query(
            user_message,
            history
        )
    else:
        search_query = user_message

    rewrite_time = (
        time.perf_counter() - rewrite_start
    )

    print(
        f"[TIME] Query rewriting: "
        f"{rewrite_time:.3f}s"
    )

    # ==================================================
    # INTENT CLASSIFICATION
    # ==================================================

    intent_start = time.perf_counter()

    intent = classify_intent(
        search_query
    )

    intent_time = (
        time.perf_counter() - intent_start
    )

    print(
        f"[TIME] Intent classification: "
        f"{intent_time:.3f}s"
    )

    print(
        f"Detected Intent : {intent.value}"
    )

    print("Original Question:")
    print(user_message)

    print("Rewritten Query:")
    print(search_query)

    # ==================================================
    # RETRIEVAL
    # ==================================================

    retrieval_k = (
        6
        if intent == Intent.EVALUATION
        else 3
    )

    context, results, retrieval_time = build_context(
        search_query,
        top_k=retrieval_k,
        intent=intent.value
    )

    # ==================================================
    # CONFIDENCE
    # ==================================================

    confidence_start = time.perf_counter()

    confidence = calculate_retrieval_confidence(
        results
    )

    confidence_time = (
        time.perf_counter() - confidence_start
    )

    print(
        f"[TIME] Confidence calculation: "
        f"{confidence_time:.3f}s"
    )

    print(
        f"Retrieval confidence: "
        f"{confidence:.3f}"
    )

    # ==================================================
    # RAG PROMPT
    # ==================================================

    rag_prompt = f"""
RETRIEVED PORTFOLIO INFORMATION
================================

{context}

CONFIDENCE INFORMATION
======================

Retrieval confidence:
{confidence:.3f}

Use the retrieved portfolio information above to answer
the recruiter's question.

IMPORTANT:
- Prefer information from the retrieved portfolio sources.
- Do not invent information.
- Do not infer unstated employers, technologies,
  responsibilities, dates, or qualifications.
- If the user's question contains a false premise (e.g., asking about
  a company, project, or technology not in the portfolio), explicitly 
  correct the premise before answering.
- If the retrieved information does not contain enough evidence,
  say that the portfolio does not provide enough information.
"""

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "system",
            "content": rag_prompt
        }
    ]

    messages.extend(history)

    messages.append(
        {
            "role": "user",
            "content": user_message
        }
    )

    build_messages_time = (
        time.perf_counter() - total_start
    )

    print(
        f"[TIME] build_messages total: "
        f"{build_messages_time:.3f}s"
    )

    return (
        messages,
        context,
        intent,
        results,
        confidence
    )


def requires_evidence_verification(
    user_message: str,
    intent: Intent,
    confidence: float
) -> bool:

    text = user_message.lower()

    sensitive_phrases = (
        "worked at",
        "worked with",
        "experience with",
        "does he know",
        "does he have",
        "has he",
        "can he",
        "did he",
        "years of experience",
        "production experience",
    )

    return (
        confidence < 0.75
        or intent == Intent.EVALUATION
        or any(
            phrase in text
            for phrase in sensitive_phrases
        )
    )


def requires_grounding(
    user_message: str,
    intent: Intent,
    confidence: float,
    results: list[dict]
) -> bool:

    text = user_message.lower()

    risky_phrases = (
        "worked at",
        "worked with",
        "experience with",
        "does he know",
        "does he have",
        "has he",
        "can he",
        "years of experience",
        "production experience",
        "suitable",
        "good candidate",
        "fit for",
        "hire",
    )

    return (
        confidence < 0.75
        or intent == Intent.EVALUATION
        or len(results) > 3
        or any(
            phrase in text
            for phrase in risky_phrases
        )
    )


def chat(
    user_message: str,
    history: list[dict]
) -> str:

    total_start = time.perf_counter()

    # ==================================================
    # COMPOUND QUESTION PATH
    # ==================================================

    if is_likely_compound(user_message):

        decomposition_start = time.perf_counter()

        subquestions = decompose_question(
            user_message
        )

        decomposition_time = (
            time.perf_counter()
            - decomposition_start
        )

        print(
            f"[TIME] Question decomposition: "
            f"{decomposition_time:.3f}s"
        )

        print(
            f"Subquestions: {subquestions}"
        )

        if len(subquestions) > 1:

            subresults = []

            for i, question in enumerate(subquestions):
                if i > 0:
                    print("Throttling API request (2s)...")
                    time.sleep(2)

                print(
                    f"\nProcessing sub-question: "
                    f"{question}"
                )

                subresult = process_subquestion(
                    question,
                    history
                )

                subresults.append(
                    subresult
                )

            # ------------------------------------------
            # Build one final synthesis request
            # ------------------------------------------

            synthesis_messages = build_compound_messages(
                user_message,
                history,
                subresults
            )

            generation_start = time.perf_counter()

            answer = generate_response(
                synthesis_messages
            )

            generation_time = (
                time.perf_counter()
                - generation_start
            )

            print(
                f"[TIME] Compound answer generation: "
                f"{generation_time:.3f}s"
            )

            answer = clean_model_output(
                answer
            )

            print(
                "\nCOMPOUND ANSWER"
            )
            print("=" * 60)
            print(answer)
            print("=" * 60)

            return answer


    # ==================================================
    # BUILD PIPELINE
    # ==================================================

    messages, context, intent, results, confidence = build_messages(
        user_message,
        history
    )

    # ==================================================
    # ABSTENTION
    # ==================================================

    abstention_start = time.perf_counter()

    abstain = should_abstain(
        results,
        confidence
    )

    abstention_time = (
        time.perf_counter() - abstention_start
    )

    print(
        f"[TIME] Abstention check: "
        f"{abstention_time:.3f}s"
    )

    if abstain:

        total_time = (
            time.perf_counter() - total_start
        )

        print(
            f"\n[TIME] TOTAL CHAT: "
            f"{total_time:.3f}s"
        )

        return (
            "I couldn't verify that information against "
            "Suryansh's portfolio. The available portfolio "
            "evidence is not sufficient to answer that "
            "confidently."
        )

    # ==================================================
    # EVIDENCE VERIFICATION
    # ==================================================

    if requires_evidence_verification(
        user_message,
        intent,
        confidence
    ):

        evidence_start = time.perf_counter()

        evidence = verify_evidence(
            user_message,
            context
        )

        evidence_time = (
            time.perf_counter() - evidence_start
        )

        print(
            f"[TIME] Evidence verification: "
            f"{evidence_time:.3f}s"
        )

        print(
            f"Evidence Supported: "
            f"{evidence['supported']}"
        )

        print(
            f"Evidence reason: "
            f"{evidence['reason']}"
        )

        if not evidence["supported"]:
            print("Evidence unsupported. Bypassing specific intent and routing to conversational LLM for correction.")
            messages.append({
                "role": "system",
                "content": f"EVIDENCE VERIFICATION FAILED: {evidence['reason']}\n\nThe user's query contains a false premise. You MUST explicitly correct them using the failure reason above in your final answer."
            })
            intent = Intent.FACTUAL

    else:

        print(
            "[TIME] Evidence verification: skipped"
        )

    # ==================================================
    # EVALUATION PATH
    # ==================================================

    if intent == Intent.EVALUATION:

        role_start = time.perf_counter()

        roles = extract_roles(
            user_message
        )

        role_time = (
            time.perf_counter() - role_start
        )

        print(
            f"[TIME] Role extraction: "
            f"{role_time:.3f}s"
        )

        print(
            f"Evaluation Roles: {roles}"
        )

        if not roles:
            print("No specific roles extracted. Defaulting to 'General Fit'.")
            roles = ["General Fit"]

        evaluations = []

        evaluation_start = time.perf_counter()

        for i, role in enumerate(roles):
            if i > 0:
                print("Throttling API request (2s)...")
                time.sleep(2)

            print(
                f"Evaluating role: {role}"
            )

            evaluation = evaluate_candidate(
                role,
                context
            )

            evaluations.append(
                evaluation
            )

        evaluation_time = (
            time.perf_counter() - evaluation_start
        )

        print(
            f"[TIME] Candidate evaluation: "
            f"{evaluation_time:.3f}s"
        )

        total_time = (
            time.perf_counter() - total_start
        )

        print(
            f"\n[TIME] TOTAL CHAT: "
            f"{total_time:.3f}s"
        )

        return format_multi_evaluation(
            evaluations
        )

    # ==================================================
    # FINAL LLM ANSWER
    # ==================================================

    generation_start = time.perf_counter()

    answer = generate_response(
        messages
    )

    generation_time = (
        time.perf_counter() - generation_start
    )

    print(
        f"[TIME] Final answer generation: "
        f"{generation_time:.3f}s"
    )

    # Clean exposed <think> blocks before anything else.
    answer = clean_model_output(
        answer
    )

    print("\nGENERATED ANSWER CLEANED")
    print("=" * 60)
    print(repr(answer))
    print("=" * 60)

    # ==================================================
    # EMPTY RESPONSE SAFETY
    # ==================================================

    if not answer:

        total_time = (
            time.perf_counter() - total_start
        )

        print(
            f"\n[TIME] TOTAL CHAT: "
            f"{total_time:.3f}s"
        )

        return (
            "I found relevant information in "
            "Suryansh's portfolio, but I couldn't "
            "generate a response. Please try again."
        )

    # ==================================================
    # GROUNDING VERIFICATION
    # ==================================================

    if requires_grounding(
        user_message,
        intent,
        confidence,
        results
    ):

        grounding_start = time.perf_counter()

        grounding = check_grounding(
            user_message,
            answer,
            context
        )

        grounding_time = (
            time.perf_counter() - grounding_start
        )

        print(
            f"[TIME] Grounding verification: "
            f"{grounding_time:.3f}s"
        )

        print(
            f"Grounding Verdict: "
            f"{grounding['verdict']}"
        )

        print(
            f"Grounding Reason: "
            f"{grounding['reason']}"
        )

        if grounding["verdict"] == "SUPPORTED":

            total_time = (
                time.perf_counter() - total_start
            )

            print(
                f"\n[TIME] TOTAL CHAT: "
                f"{total_time:.3f}s"
            )

            return answer

        if grounding["verdict"] == "PARTIALLY_SUPPORTED":

            total_time = (
                time.perf_counter() - total_start
            )

            print(
                f"\n[TIME] TOTAL CHAT: "
                f"{total_time:.3f}s"
            )

            return (
                answer
                + "\n\n"
                + "Note: Some details in this answer "
                  "could not be fully verified against "
                  "the portfolio."
            )

        total_time = (
            time.perf_counter() - total_start
        )

        print(
            f"\n[TIME] TOTAL CHAT: "
            f"{total_time:.3f}s"
        )

        return (
            "I couldn't verify that information "
            "against Suryansh's portfolio. "
            "The portfolio does not provide sufficient "
            "evidence to answer that confidently."
        )

    else:

        print(
            "[TIME] Grounding verification: skipped"
        )

        total_time = (
            time.perf_counter() - total_start
        )

        print(
            f"\n[TIME] TOTAL CHAT: "
            f"{total_time:.3f}s"
        )

        return answer


def format_multi_evaluation(
    evaluations: list[dict]
) -> str:

    sections = []

    for evaluation in evaluations:

        sections.append(
            format_evaluation(
                evaluation
            )
        )

    return (
        "## Candidate Assessment\n\n"
        + "\n\n---\n\n".join(
            sections
        )
    )


def _format_item(item) -> str:
    """Helper to cleanly format list items, joining dict values if necessary."""
    if isinstance(item, dict):
        return " — ".join(str(v) for v in item.values() if v)
    return str(item)


def format_evaluation(
    evaluation: dict
) -> str:

    role = evaluation.get(
        "role",
        "the role"
    )

    assessment = evaluation.get(
        "overall_assessment",
        "Unable to determine"
    )

    matched_skills = evaluation.get(
        "matched_skills",
        []
    )

    experience = evaluation.get(
        "relevant_experience",
        []
    )

    projects = evaluation.get(
        "relevant_projects",
        []
    )

    not_established = evaluation.get(
        "not_established",
        []
    )

    reasoning = evaluation.get(
        "reasoning",
        ""
    )

    response = f"""
## Candidate Assessment: {role}

**Overall assessment:** {assessment}

### Relevant skills
"""

    if matched_skills:

        for item in matched_skills:
            response += f"- {_format_item(item)}\n"

    else:

        response += (
            "- No specific matches established.\n"
        )

    response += (
        "\n### Relevant experience\n"
    )

    if experience:

        for item in experience:
            response += f"- {_format_item(item)}\n"

    else:

        response += (
            "- No directly relevant experience established.\n"
        )

    response += (
        "\n### Relevant projects\n"
    )

    if projects:

        for item in projects:
            response += f"- {_format_item(item)}\n"

    else:

        response += (
            "- No directly relevant projects established.\n"
        )

    response += (
        "\n### Not established by the portfolio\n"
    )

    if not_established:

        for item in not_established:
            response += f"- {_format_item(item)}\n"

    else:

        response += "- None identified.\n"

    response += (
        f"\n### Assessment\n{reasoning}"
    )

    return response.strip()


def stream_chat(
    user_message: str,
    history: list[dict]
) -> Iterator[str]:

    total_start = time.perf_counter()

    # ----------------------------------------------
    # Compound Query Handling for Streams
    # ----------------------------------------------
    if is_likely_compound(user_message):
        subquestions = decompose_question(user_message)
        if len(subquestions) > 1:
            subresults = []
            for i, question in enumerate(subquestions):
                if i > 0:
                    print("Throttling API request (2s)...")
                    time.sleep(2)
                subresults.append(process_subquestion(question, history))

            synthesis_messages = build_compound_messages(user_message, history, subresults)
            
            stream_filter = ThinkStreamFilter()
            full_response = ""
            generation_start = time.perf_counter()
            for chunk in generate_response_stream(synthesis_messages):
                visible_text = stream_filter.feed(chunk)
                if visible_text:
                    full_response += visible_text
                    yield visible_text
            
            remaining = stream_filter.flush()
            if remaining:
                full_response += remaining
                yield remaining
            print(f"[TIME] Compound stream generation: {time.perf_counter() - generation_start:.3f}s")
            return

    messages, context, intent, results, confidence = build_messages(
        user_message,
        history
    )

    # ----------------------------------------------
    # Abstention
    # ----------------------------------------------

    if should_abstain(
        results,
        confidence
    ):

        yield (
            "I couldn't verify that information against "
            "Suryansh's portfolio. The available portfolio "
            "evidence is not sufficient to answer that confidently."
        )

        return

    # ----------------------------------------------
    # Evidence verification
    # ----------------------------------------------

    if requires_evidence_verification(
        user_message,
        intent,
        confidence
    ):

        evidence_start = time.perf_counter()

        evidence = verify_evidence(
            user_message,
            context
        )

        print(
            f"[TIME] Evidence verification: "
            f"{time.perf_counter() - evidence_start:.3f}s"
        )

        if not evidence["supported"]:
            print("Evidence unsupported. Bypassing specific intent and routing to conversational LLM for correction.")
            messages.append({
                "role": "system",
                "content": f"EVIDENCE VERIFICATION FAILED: {evidence['reason']}\n\nThe user's query contains a false premise. You MUST explicitly correct them using the failure reason above in your final answer."
            })
            intent = Intent.FACTUAL

    # ----------------------------------------------
    # Evaluation
    # ----------------------------------------------

    if intent == Intent.EVALUATION:

        roles = extract_roles(user_message)

        if not roles:
            print("No specific roles extracted. Defaulting to 'General Fit'.")
            roles = ["General Fit"]

        evaluations = []
        for i, role in enumerate(roles):
            if i > 0:
                print("Throttling API request (2s)...")
                time.sleep(2)
            evaluations.append(evaluate_candidate(role, context))

        yield format_multi_evaluation(evaluations)
        return

    # ----------------------------------------------
    # Stream final answer
    # ----------------------------------------------

    stream_filter = ThinkStreamFilter()
    full_response = ""

    generation_start = time.perf_counter()

    for chunk in generate_response_stream(
        messages
    ):

        visible_text = stream_filter.feed(
            chunk
        )

        if visible_text:

            full_response += visible_text

            yield visible_text

    remaining = stream_filter.flush()

    if remaining:

        full_response += remaining

        yield remaining

    print(
        f"[TIME] Streaming generation: "
        f"{time.perf_counter() - generation_start:.3f}s"
    )

    print(
        f"[TIME] TOTAL STREAM CHAT: "
        f"{time.perf_counter() - total_start:.3f}s"
    )