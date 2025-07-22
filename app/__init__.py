from flask import Flask
from flask_wtf.csrf import CSRFProtect
import os
import markdown
from markupsafe import Markup

# Handle zoneinfo import for different Python versions
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


def create_app(config_name=None):
    app = Flask(__name__)

    # Configuration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["WTF_CSRF_ENABLED"] = True
    app.config["WTF_CSRF_TIME_LIMIT"] = None

    # Session configuration
    app.config["MAX_COOKIE_SIZE"] = 131072  # 128KB instead of 64KB to handle large question data
    app.config["SESSION_COOKIE_SECURE"] = False  # Set to True in production with HTTPS
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour in seconds

    # Timezone configuration
    app.config["TIMEZONE"] = ZoneInfo("Europe/Paris")

    # Initialize CSRF protection
    CSRFProtect(app)

    # Add markdown filter
    @app.template_filter('markdown')
    def markdown_filter(text):
        """Convert markdown text to HTML."""
        if not text:
            return ""
        return Markup(markdown.markdown(text, extensions=['nl2br']))

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; img-src 'self' https:;"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    # Register blueprints
    from app.routes.national import national_bp
    from app.routes.personal import personal_bp
    from app.routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(national_bp, url_prefix="/national")
    app.register_blueprint(personal_bp, url_prefix="/personnel")

    return app
