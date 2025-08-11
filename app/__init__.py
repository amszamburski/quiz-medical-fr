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

    @app.template_filter('inline_bold')
    def inline_bold_filter(text):
        """Render inline bold markers from Topic strings.

        - Converts **bold** to <strong>bold</strong>
        - Leaves existing HTML <b>/<strong> as-is
        - Does not wrap in <p> (keeps inline)
        """
        if not text:
            return ""
        import re
        s = str(text)
        # Replace Markdown-style bold with strong tags
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return Markup(s)

    @app.template_filter('topic_parts')
    def topic_parts_filter(text):
        """Split a Topic string into (title, subtitle).

        Prefer bold-marked title (between ** **). If none, split at first colon.
        Returns a 2-tuple of plain strings: (title, subtitle).
        """
        if not text:
            return ("", "")
        import re
        s = str(text)
        # If markdown bold present, use first bold span as title
        m = re.search(r"\*\*(.+?)\*\*", s)
        if m:
            title = m.group(1).strip()
            # Remove the bold markers and title from the text to get remainder
            remainder = (s[:m.start()] + s[m.end():]).strip()
            # Strip common separators at start
            remainder = remainder.lstrip(" :–—-\u2013\u2014")
            return (title, remainder.strip())
        # Fallback: split at colon
        if ":" in s:
            left, right = s.split(":", 1)
            return (left.strip(), right.strip())
        return (s.strip(), "")

    @app.template_filter('normalize_link')
    def normalize_link_filter(value):
        """Normalize link/DOI values to clickable URLs.

        - Strips whitespace and trailing punctuation
        - Converts "doi:10.xxxx/yyy" or "10.xxxx/yyy" to https://doi.org/...
        - Adds https scheme to bare www.* links
        """
        try:
            import re
            s = str(value or "").strip()
            if not s or s.lower() == "nan":
                return ""
            s = s.rstrip(".,); ")
            # Handle doi: prefix
            if s.lower().startswith("doi:"):
                s = s.split(":", 1)[1].strip()
            # Raw DOI
            if re.match(r"^10\.\d{4,9}/\S+", s):
                return f"https://doi.org/{s}"
            # Bare domain
            if s.startswith("www."):
                return f"https://{s}"
            # Already a URL
            if s.startswith("http://") or s.startswith("https://"):
                return s
            return s
        except Exception:
            return ""

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
