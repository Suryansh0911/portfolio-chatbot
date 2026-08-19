from app.services.chatbot import chat


TEST_QUESTIONS = [
    "What NLP projects has Suryansh built?",
    "What did Suryansh do during his internship?",
    "What technologies does Suryansh know?",
    "What are Suryansh's educational qualifications?",
    "What machine learning experience does Suryansh have?"
]


for question in TEST_QUESTIONS:

    print("\n" + "=" * 80)

    print("QUESTION:")
    print(question)

    answer = chat(
        question,
        history=[]
    )

    print("\nANSWER:")
    print(answer)