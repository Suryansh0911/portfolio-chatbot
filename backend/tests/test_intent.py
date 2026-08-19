from app.rag.intent_classifier import classify_intent


questions = [

    "What technologies does Suryansh know?",

    "What projects has Suryansh built?",

    "What did he do during his internship?",

    "Give me a short summary of his profile.",

    "Would he be a good candidate for an ML Engineer role?",

    "Tell me something about Suryansh."

]


for question in questions:

    intent = classify_intent(
        question
    )

    print(
        f"\nQuestion: {question}"
    )

    print(
        f"Intent: {intent.value}"
    )