# Code Analyst Agent &nbsp;![CI](https://github.com/anythingai/code-analyst-agent/actions/workflows/ci.yml/badge.svg)

A multi-agent system powered by Gemini 2.5 Pro (via Google Vertex AI) for deep, context-rich analysis of large software codebases.

---

## Features

* Orchestrated agents for parsing, security scanning, and performance profiling
* Handles monolithic and micro-service repositories up to ~500 kLOC
* Generates actionable security, performance, and architectural insights
* Outputs reports in **JSON, HTML, Markdown, PDF and DOCX** formats
* CLI and Flask API for flexibility

## Quick Start

```bash
# Clone and enter your repo directory
pip install -e .  # installs package in editable mode

codebase-analyze --repo <REPO_URL_OR_PATH> --output report \
                 --formats json,html,md,pdf,docx

# Or run the API
export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
python -m codebase_analysis.api  # serves on http://localhost:8000
# Open your browser at http://localhost:8000 to use the interactive web UI.
```

## Installation

1. Ensure Python ≥ 3.9 is installed.
2. (Recommended) create a virtual-environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. Install the package and its pure-Python report dependencies:

   ```bash
   pip install -e .
   ```

4. Create an `.env` file (see `.env.example`) and add your GCP and NVD credentials.
   • To enable Redis-backed rate limiting set `RATELIMIT_STORAGE_URL=redis://:<pass>@<host>:6379/0`.
   • Set `LOG_FORMAT=json` for structured logs (Stackdriver-friendly).
   • Change `REPORT_DIR=/mnt/reports` if you want reports in a mounted volume.

### Runtime configuration

| Variable | Purpose | Default |
| -------- | ------- | ------- |
| `GOOGLE_API_KEY` **or** `GOOGLE_CLOUD_PROJECT` | Required for live Gemini 2.5 Pro calls | *(none)* |
| `NVD_API_KEY` | Required for CVE look-ups against NVD | *(none)* |
| `REPORT_DIR` | Where generated files are saved | `./reports` |
| `RATELIMIT_STORAGE_URL` | Redis/Memcached DSN for Flask-Limiter | `memory://` |
| `LOG_FORMAT` | `rich` (colour) or `json` | `rich` |

The API exposes **`/healthz`** for load-balancer readiness probes.

### Docker

The multi-stage image already bundles `fpdf2` & `python-docx`, so PDF/DOCX export works without system libraries.

```bash
docker build -t codebase-analysis:latest .
docker run -p 8000:8000 codebase-analysis:latest
```

 Build and run the container:

```bash
docker build -t codebase-analysis:latest .
# Runs gunicorn with 4 workers exposing port 8000
docker run -p 8000:8000 codebase-analysis:latest
```

## Project Structure

``` text
codebase_analysis/
  agents/        # individual agent implementations
  tools/         # code understanding, CVE querying, etc.
  report/        # report generator and templates
  orchestrator.py
  cli.py
  api.py         # Flask wrapper
```

---
