import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

db = SQLAlchemy()
def create_app():
    load_dotenv()
    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "minbook-local-key")

    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    database_path = os.path.join(base_dir, "minbook.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("ACCOUNTING_DATABASE_URL", "sqlite:///" + database_path)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SHOPPOS_DATABASE_URL"] = os.getenv("SHOPPOS_DATABASE_URL", "")

    db.init_app(app)
    from app.routes import main
    app.register_blueprint(main)

    with app.app_context():
        db.create_all()

    return app
