from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    JWTManager(app)

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