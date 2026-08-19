from app.services.chatbot import chat


history = []


questions = [
    "What NLP projects has Suryansh built?",
    "Which one uses Hugging Face?",
    "What technologies does that project use?"
]


for question in questions:

    print("\n" + "=" * 80)
    print("USER:")
    print(question)

    answer = chat(
        question,
        history
    )

    print("\nASSISTANT:")
    print(answer)

    history.append({
        "role": "user",
        "content": question
    })

    history.append({
        "role": "assistant",
        "content": answer
    })