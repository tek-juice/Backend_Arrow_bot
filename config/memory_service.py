from models.user import ChatMessage
def get_last_messages(session_id, limit=10):
    return ChatMessage.query.filter_by(
        session_id=session_id
    ).order_by(ChatMessage.created_at.asc()).all()[-limit:]


def format_messages(messages):
    return [
        {
            "role": "user" if m.sender == "user" else "assistant",
            "content": m.content
        }
        for m in messages
    ]

def build_chat_session(session_id, question):
    messages = get_last_messages(session_id, 10)
    history = format_messages(messages)

    history.append({
        "role": "user",
        "content": question
    })

    return history