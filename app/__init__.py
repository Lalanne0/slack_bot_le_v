from flask import Flask
import config

def create_app():
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = "data/uploads"
    app.secret_key = config.SECRET_KEY

    with app.app_context():
        from .routes import register_routes
        register_routes(app)

    return app
