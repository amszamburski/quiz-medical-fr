from flask import Blueprint, render_template

personal_bp = Blueprint("personal", __name__)


@personal_bp.route("/")
def index():
    return render_template("personal/index.html")
