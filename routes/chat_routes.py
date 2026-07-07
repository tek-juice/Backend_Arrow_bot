from flask import Blueprint, request, Response, stream_with_context, jsonify
from config.session_message_service import save_message, get_or_create_session
from config.nvidia import stream_answer
from models.user import ChatMessage, ChatSession
from flasgger import swag_from
from config.extensions import db
from datetime import datetime
from config.limiter import limiter

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
@limiter.limit("38 per miniute")
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Ask the AI assistant a question",
    "description": "Uses pgvector retrieval + NVIDIA LLM to answer questions based on your knowledge base. Response is streamed token-by-token.",
    
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "example": "What is the conveyancing process?"
                    }
                },
                "required": ["question"]
            }
        }
    ],

    "responses": {
        200: {
            "description": "Streaming AI response (text/plain token stream)"
        },
        400: {
            "description": "Validation error - missing question"
        },
        500: {
            "description": "Server error"
        }
    }
})
def chat():

    data = request.get_json() or {}

    question = data.get("question")
    session_uuid = data.get("session_id")

    if not question:
        return jsonify({"error": "A question is required"}), 400

    session = get_or_create_session(session_uuid)

    save_message(
        session_id=session.id,
        sender="user",
        content=question
    )

    def generate():

        full_response = ""

        for token in stream_answer(session.id, question):

            full_response += token
            yield token

        save_message(
            session_id=session.id,
            sender="assistant",
            content=full_response
        )

    return Response(
        stream_with_context(generate()),
        mimetype="text/plain",
        headers={
             "X-Session-Id": session.session_uuid,
            "X-Accel-Buffering": "no",
        },
    )

@chat_bp.route("/chat/history/<session_uuid>", methods=["GET"])
@swag_from({
    "tags": ["Chatbot"],
    "summary": "Get chat history for a session",
    "description": "Retrieves all messages (user and assistant) for a given chat session UUID.",
    
    "parameters": [
        {
            "name": "session_uuid",
            "in": "path",
            "required": True,
            "type": "string",
            "example": "550e8400-e29b-41d4-a716-446655440000"
        }
    ],

    "responses": {
        200: {
            "description": "Chat history retrieved successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "session_id": {"type": "string"},
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "messages": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "role": {"type": "string", "example": "user"},
                                "content": {"type": "string"},
                                "created_at": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Session not found"
        }
    }
})
def get_chat_history(session_uuid):
    session = ChatSession.query.filter_by(
        session_uuid = session_uuid
    ).first()

    if not session:
        return jsonify({
            "error": "session not found"
        }), 404
    
    messages = ChatMessage.query.filter_by(
        session_id=session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    return jsonify({
        "session_id": session.session_uuid,
        "name": session.name,
        "email": session.email,
        "messages": [
            {
                "id": msg.id,
                "role": msg.sender,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }

            for msg in messages
        ]
    }),200

@chat_bp.route("/chat/session/<session_uuid>", methods=["PUT"])
@swag_from({
    "tags": ["Chat Session"],
    "description": "Update session name and email using session_uuid",
    "parameters": [
        {
            "name": "session_uuid",
            "in": "path",
            "required": True,
            "type": "string"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"}
                }
            }
        }
    ],
    "responses": {
        "200": {"description": "Session updated successfully"},
        "404": {"description": "Session not found"}
    }
})
def update_session(session_uuid):
    data = request.get_json() or {}

    name = data.get("name")
    email = data.get("email")

    session= ChatSession.query.filter_by(
        session_uuid=session_uuid
    ).first()

    if not session:
        return jsonify({
            "error": "session not found"
        }), 404
    
    if name:
        session.name =  name
    
    if email:
        session.email = email

    session.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        "message": "Name and email updated succefully",
        "session": {
            "session_uuid": session_uuid,
            "name": session.name,
            "email": session.email
        }
    }), 200

@chat_bp.route("/users", methods=["GET"])
@swag_from({
    "tags": ["Admin Chat"],
    "summary": "Get all chat sessions",
    "description": "Returns all chat sessions ordered by most recently updated.",
    "responses": {
        200: {
            "description": "List of chat sessions"
        }
    }    
})

def get_chat_sessions():
    sessions = ChatSession.query.order_by(
        ChatSession.updated_at.desc()
    ).all()

    return jsonify([
        {
            "session_uuid": session.session_uuid,
            "name": session.name,
            "email": session.email,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "message_count": len(session.messages)
        }
        for session in sessions
    ]), 200

@chat_bp.route("/users/<string:session_uuid>", methods=["GET"])
@swag_from({
    "tags": ["Admin Chat"],
    "summary": "Get a chat session",
    "description": "Returns a chat session together with all exchanged messages.",
    "parameters": [
        {
            "name": "session_uuid",
            "in": "path",
            "required": True,
            "schema": {
                "type": "string"
            }
        }
    ],
    "responses": {
        200: {
            "description": "Chat session and messages"
        },
        404: {
            "description": "Session not found"
        }
    }
})

def get_chat_session_messages(session_uuid):

    session = ChatSession.query.filter_by(
        session_uuid=session_uuid
    ).first()

    if not session:
        return jsonify({
            "error": "Session not found"
        }), 404

    messages = ChatMessage.query.filter_by(
        session_id=session.id
    ).order_by(ChatMessage.created_at.asc()).all()

    return jsonify({
        "session_uuid": session.session_uuid,
        "name": session.name,
        "email": session.email,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "message_count": len(messages),

        "messages": [
            {
                "id": msg.id,
                "sender": msg.sender,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }), 200