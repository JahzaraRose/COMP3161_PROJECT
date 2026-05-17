from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from app.authz import safe_error
import os
import mysql.connector

load_dotenv()


def _env_flag(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def create_app():
    app = Flask(__name__)
    jwt_secret = os.getenv("JWT_SECRET_KEY")
    if not jwt_secret and not _env_flag("FLASK_DEBUG"):
        raise RuntimeError("JWT_SECRET_KEY must be set in production")

    app.config["JWT_SECRET_KEY"] = jwt_secret or "development-only-secret"

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    JWTManager(app)

    @app.errorhandler(mysql.connector.Error)
    def handle_mysql_error(error):
        return safe_error(error, status=500)

    from app.routes.auth        import auth_bp
    from app.routes.courses     import courses_bp
    from app.routes.enrollments import enrollments_bp
    from app.routes.content     import content_bp
    from app.routes.assignments import assignments_bp
    from app.routes.calendar    import calendar_bp
    from app.routes.forums      import forums_bp
    from app.routes.reports     import reports_bp

    app.register_blueprint(auth_bp,        url_prefix="/api")
    app.register_blueprint(courses_bp,     url_prefix="/api")
    app.register_blueprint(enrollments_bp, url_prefix="/api")
    app.register_blueprint(content_bp,     url_prefix="/api")
    app.register_blueprint(assignments_bp, url_prefix="/api")
    app.register_blueprint(calendar_bp,    url_prefix="/api")
    app.register_blueprint(forums_bp,      url_prefix="/api")
    app.register_blueprint(reports_bp,     url_prefix="/api")

    return app
