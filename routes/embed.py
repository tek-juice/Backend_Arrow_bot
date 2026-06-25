from flask import Blueprint, request, jsonify
from config.extensions import db
from models.user import DocumentChunk
from config.embeddings import get_embedding
from flasgger import swag_from

ingest_bp =  Blueprint("ingest",__name__)

@ingest_bp.route("/ingest", methods=["POST"])
@swag_from({
    "tags": ["Vector Database"],
    "summary": "Ingest a document into the vector database",
    "description": "Chunks the document, generates BGE embeddings, and stores them in PostgreSQL.",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "example": "Arrow Conveyancing Services"
                    },
                    "text": {
                        "type": "string",
                        "example": "Arrow Conveyancing offers residential and commercial property conveyancing..."
                    }
                },
                "required": ["title", "text"]
            }
        }
    ],
    "responses": {
        201: {
            "description": "Document ingested successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "example": "document ingested successfully"
                    },
                    "chunks_saved": {
                        "type": "integer",
                        "example": 5
                    }
                }
            }
        },
        400: {
            "description": "Validation error",
            "schema": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "string",
                        "example": "title and text are required"
                    }
                }
            }
        }
    }
})
def ingest_document():
    data = request.get_json() or {}

    title = data.get("title")
    text = data.get("text")

    if not title or not text:
        return jsonify({"error": "title and text are required"}), 400
    
    chunks = [text[i:i+800]for i in range(0, len(text), 800)]
    saved_count = 0

    for chunk in chunks:
        embedding = get_embedding(chunk)

        doc = DocumentChunk(
            title=title,
            chunk=chunk,
            embedding=embedding
        )

        db.session.add(doc)
        saved_count += 1

    db.session.commit()

    return jsonify({
        "message": "document ingested successfully",
        "chunks_saved": saved_count
    })

@ingest_bp.route("/chunks", methods=["GET"])
@swag_from({
    "tags": ["Vector Database"],
    "description": "Fetch all document chunks stored in the vector database",
    "responses": {
        200: {
            "description": "List of document chunks",
            "examples": {
                "application/json": [
                    {
                        "id": 1,
                        "title": "Contract Guide",
                        "chunk": "This is a sample chunk..."
                    }
                ]
            }
        }
    }
})
def get_chunks():
    chunks = DocumentChunk.query.all()
    return jsonify([
        {
            "id": c.id,
            "title": c.title,
            "chunk": c.chunk
        }
        for c in chunks
    ])

@ingest_bp.route("/chunks<int:chunk_id>", methods=["DELETE"])
@swag_from({
    "tags": ["Vector Database"],
    "description": "Delete a document chunk and its embedding from the database",
    "parameters": [
        {
            "name": "chunk_id",
            "in": "path",
            "type": "integer",
            "required": True,
            "description": "ID of the document chunk to delete"
        }
    ],
    "responses": {
        200: {
            "description": "Chunk deleted successfully"
        },
        404: {
            "description": "Chunk not found"
        }
    }
})
def delete_chunk(chunk_id):
    chunk = DocumentChunk.query.get(chunk_id)

    if not chunk:
        return jsonify({
            "error": "Vhunk not found"
        }), 404
    
    db.session.delete(chunk)
    db.session.commit()

    return jsonify({
        "message": "chunk deleted successfully",
        "deleted_id": chunk_id
    })