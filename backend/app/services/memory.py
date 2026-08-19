from collections import defaultdict


conversation_store = defaultdict(list)


def get_history(conversation_id: str) -> list[dict]:
    return conversation_store[conversation_id]


def add_message(
    conversation_id: str,
    role: str,
    content: str
):
    conversation_store[conversation_id].append(
        {
            "role": role,
            "content": content
        }
    )


def clear_history(conversation_id: str):
    conversation_store.pop(conversation_id, None)