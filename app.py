from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from routes.home_routes import home_bp
from routes.auth_routes import auth_bp
from routes.embed import ingest_bp

from config.extensions import db, jwt, migrate
from dotenv import load_dotenv
import os

load_dotenv()


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

    swagger = Swagger(app, config=swagger_config)

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(ingest_bp, url_prefix="/api")

    @app.route("/")
    def root():
        return {
            "status": "running",
            "docs": "/apidocs/"
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
        threaded=True,
        use_reloader=False
    )