from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from routes.chat_routes import chat_bp
from routes.debug_routes import debug_bp
from routes.home_routes import home_bp
from routes.auth_routes import auth_bp
from extensions import db, jwt, migrate
from dotenv import load_dotenv
import os

load_dotenv()

from warmModel import warmup_model

def create_app():

    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    print("DATABASE_URL:", os.getenv("DATABASE_URL"))
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    CORS(app)

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    Swagger(app, config=swagger_config)

    app.register_blueprint(home_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(debug_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")

    warmup_model()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        threaded=True,
        port=5000,
        use_reloader=False
    )