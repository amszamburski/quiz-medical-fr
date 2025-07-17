from flask import Blueprint, render_template

national_bp = Blueprint("national", __name__)


@national_bp.route("/")
def index():
    return render_template("national/index.html")
