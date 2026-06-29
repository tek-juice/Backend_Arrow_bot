from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from config.extensions import db
from pgvector.sqlalchemy import Vector
import uuid


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    names = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_anonymous = db.Column( db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class DocumentChunk(db.Model):
    __tablename__ = "document_chunks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    chunk = db.Column(db.Text, nullable=False)

    embedding = db.Column(Vector(384), nullable=False)

    def __repr__(self):
        return f"<DocumentChunk {self.title}>"
    
class ChatSession(db.Model):
    __tablename__="chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    session_uuid = db.Column(db.String(100), unique=True, nullable=False, index=True, default=lambda: str(uuid.uuid4()),)
    name = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    messages = db.relationship("ChatMessage", backref="session", lazy=True, cascade="all, delete-orphan", order_by="ChatMessage.created_at",)


class ChatMessage(db.Model):
    __tablename__="chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    sender = db.Column(db.String(250), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

