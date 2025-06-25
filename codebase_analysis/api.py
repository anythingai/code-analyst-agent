"""Flask API wrapper to expose /analyze endpoint."""
from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

from flask import Flask
from flask import Response
from flask import abort
from flask import jsonify
from flask import request
from flask import send_file
from git import Repo

from .agents import ParserAgent
from .agents import PerformanceAgent
from .agents import SecurityAgent
from .logging_utils import setup_logging
from .orchestrator import Orchestrator
from .webui import web_bp

try:
    from flask_cors import CORS  # type: ignore
except ImportError:
    CORS = None  # pragma: no cover

# Optional rate-limiting support
try:
    from flask_limiter import Limiter  # type: ignore
    from flask_limiter.util import get_remote_address  # type: ignore
except ImportError:  # pragma: no cover
    Limiter = None  # type: ignore

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

if CORS is not None:
    CORS(app)

app.register_blueprint(web_bp)

# Initialise coloured logging for the API context as early as possible.
setup_logging()

# Directory where generated report files will be stored. Can be overridden via
# the REPORT_DIR environment variable so operators can mount a shared volume.
REPORT_DIR = Path(os.getenv("REPORT_DIR", "reports")).resolve()
REPORT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------- Security / Ops middleware ----------------------- #

# Apply simple rate limiting if flask-limiter is available.
if Limiter is not None:  # pragma: no cover – optional dependency
    storage_uri = os.getenv("RATELIMIT_STORAGE_URL")
    limiter_kwargs = {
        "key_func": get_remote_address,
        "app": app,
        "default_limits": ["60/minute"],
    }
    limiter_kwargs["storage_uri"] = storage_uri or "memory://"  # explicit to avoid warnings
    Limiter(**limiter_kwargs)  # type: ignore[arg-type]

# Set security headers on every response
@app.after_request
def set_security_headers(resp: Response):  # pragma: no cover
    resp.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline';"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    return resp

# Health-check endpoint for Cloud Run / Kubernetes probes
@app.route("/healthz")
def healthz():  # pragma: no cover
    return "ok", 200

@app.route("/analyze", methods=["POST"])
def analyze():
    """Primary analysis endpoint.

    Accepts JSON payload: {"repo_url": "...", "output": "basename", "formats": [..]}
    The repo can be a local path (already cloned) *or* a remote HTTPS/Git URL.
    We generate reports under REPORT_DIR/<uuid4>-<basename>.* to avoid filename
    clashes between concurrent requests.
    """

    data: dict[str, str] = request.get_json(force=True)
    repo_url = data.get("repo_url")
    if not repo_url:
        return {"error": "repo_url is required"}, 400

    # ---------- Determine repo path (local vs remote) ---------- #
    tmp_repo_ctx: tempfile.TemporaryDirectory[str] | None = None
    if Path(repo_url).expanduser().exists():
        repo_path = Path(repo_url).expanduser().resolve()
    else:
        # Very naive validation of remote URLs to reduce attack surface.
        if not repo_url.startswith(("https://", "http://", "git@")):
            return {"error": "Unsupported repo_url protocol"}, 400
        tmp_repo_ctx = tempfile.TemporaryDirectory()
        try:
            Repo.clone_from(repo_url, tmp_repo_ctx.name)
        except Exception as exc:
            if tmp_repo_ctx is not None:
                tmp_repo_ctx.cleanup()
            return {"error": f"Failed to clone repo: {exc}"}, 400
        repo_path = Path(tmp_repo_ctx.name)

    # ---------- Prepare report output ---------- #
    output_base = data.get("output", "report")
    # Add a UUID prefix so simultaneous requests don't collide
    unique_base = REPORT_DIR / f"{uuid.uuid4().hex}-{output_base}"

    formats = data.get("formats", ["json", "html", "md", "pdf", "docx"])
    if isinstance(formats, str):
        formats = [f.strip() for f in formats.split(',') if f.strip()]

    # ---------- Run orchestrator ---------- #
    orchestrator = Orchestrator(repo_path)
    orchestrator.register_agent(ParserAgent)
    orchestrator.register_agent(SecurityAgent)
    orchestrator.register_agent(PerformanceAgent)

    results = orchestrator.run(unique_base, formats=formats)

    # Build list of filenames relative to REPORT_DIR for client download links
    report_files = [
        f"{unique_base.name}.{ext}"
        for ext in formats
        if (REPORT_DIR / f"{unique_base.name}.{ext}").exists()
    ]

    # Clean cloned repo if we created a temp dir
    if tmp_repo_ctx is not None:
        tmp_repo_ctx.cleanup()

    return jsonify({"results": results, "report_files": report_files}), 200


# ----------------------------- Downloads ----------------------------- #


@app.route("/download/<path:filename>")
def download_report(filename: str):  # pragma: no cover
    """Serve generated report files by looking under REPORT_DIR."""
    path = (REPORT_DIR / filename).resolve()
    # Prevent directory traversal
    if not path.is_file() or not str(path).startswith(str(REPORT_DIR)):
        abort(404)
    return send_file(path, as_attachment=True)


if __name__ == "__main__":  # pragma: no cover
    app.run(host="0.0.0.0", port=8000)  # nosec B104
