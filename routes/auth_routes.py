from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models.user import User
from config.extensions import db
from flasgger import swag_from
from functools import wraps

auth_bp =Blueprint("auth", __name__)

# register Admin route 
@auth_bp.route("/register-admin", methods=["POST"])
@swag_from({
    "tags": ["Auth"],
    "description": "Register a new admin user",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "names": {"type": "string"},
                    "email": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["email", "password"]
            }
        }
    ],
    "responses": {
        201: {
            "description": "Admin created successfully"
        },
        400: {
            "description": "Validation error"
        }
    }
})
def register_admin():

    data = request.get_json() or {}
    names = data.get("names")
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "error": "email and password are required"
        }), 400
    
    existing = User.query.filter_by(email=email).first()

    if existing:
        return jsonify({
            "error": "User already exists"
        }), 400
    
    admin = User(names = names, email = email, role = "admin", is_anonymous=False)
    admin.password_hash = generate_password_hash(password)

    db.session.add(admin)
    db.session.commit()

    return jsonify({
        "message": "admin created successfully"
    }), 201

# login route  
@auth_bp.route("/login", methods=["POST"])
@swag_from({
    "tags": ["Auth"],
    "description": "Login user and return JWT token",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "password": {"type": "string"}
                },
                "required": ["email", "password"]
            }
        }
    ],
    "responses": {
        200: {
            "description": "Login successful, returns JWT token"
        },
        401: {
            "description": "Invalid credentials"
        }
    }
})
def login():

    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify ({
            "error": "Invalid credetials"
        }), 401
    
    user = User.query.filter_by(email = email).first()

    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({
            "error": "Invalid credentials"
        }), 401
    
    token = create_access_token(
        identity={
            "id": user.id,
            "role": user.role
        }
    )

    return jsonify({
        "access_token": token,
        "user": {
            "id": user.id,
            "role": user.role,
            "email": user.email
        }
    })

# permission helper to acces route 
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity["role"] != "admin":
            return jsonify({
                "error": "admin only"
            }), 403
        
        return fn(*args, **kwargs)
    return wrapper



