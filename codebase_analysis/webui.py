"""Flask blueprint that serves a minimal interactive web UI."""
from __future__ import annotations

from flask import Blueprint
from flask import render_template

web_bp = Blueprint("webui", __name__)


@web_bp.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")
