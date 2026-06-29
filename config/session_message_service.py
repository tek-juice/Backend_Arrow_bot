from models.user import ChatSession, ChatMessage
from config.extensions import db



def get_or_create_session(session_uuid=None):
    """
    If a session UUID is provided, return the existing session
    or create one using that UUID.

    If no UUID is provided, create a brand-new session.
    """

    if session_uuid:
        session = ChatSession.query.filter_by(
            session_uuid=session_uuid
        ).first()

        if session:
            return session

        session = ChatSession(session_uuid=session_uuid)

    else:
        session = ChatSession()

    db.session.add(session)
    db.session.commit()

    return session


def save_message(session_id, sender, content):
    msg = ChatMessage(
        session_id=session_id,
        sender=sender,
        content=content,
    )

    db.session.add(msg)
    db.session.commit()

    return msg