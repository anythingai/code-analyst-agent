# Code Analyst Agent

A multi-agent system powered by Gemini 2.5 Pro (via Google Vertex AI) for deep, context-rich analysis of large software codebases.

---

## Features

* Orchestrated agents for parsing, security scanning, and performance profiling
* Handles monolithic and micro-service repositories up to ~500 kLOC
* Generates actionable security, performance, and architectural insights
* Outputs both JSON and beautiful HTML reports
* CLI and Flask API for flexibility

## Quick Start

```bash
# Clone and enter your repo directory
pip install -e .  # installs package in editable mode

codebase-analyze --repo <REPO_URL_OR_PATH> --output report --formats json,html,md,pdf

# Or run the API
export GOOGLE_APPLICATION_CREDENTIALS=path/to/key.json
python -m codebase_analysis.api  # serves on http://localhost:8000
# Open your browser at http://localhost:8000 to use the interactive web UI.
```

## Installation

1. Ensure Python ≥ 3.9 is installed.
2. Install system dependencies (Git, build-essentials).
3. Install Python libs:

   ```bash
   pip install -e .
   ```

4. Create an `.env` file (see `.env.example`) and add your GCP and NVD credentials.
   • To enable Redis-backed rate limiting set `RATELIMIT_STORAGE_URL=redis://:<pass>@<host>:6379/0`.
   • Set `LOG_FORMAT=json` for structured logs (Stackdriver-friendly).
   • Change `REPORT_DIR=/mnt/reports` if you want reports in a mounted volume.

5. (Optional) Build and run the container:

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

## Contributing

Pull requests are welcome! Please run `pytest` and `ruff` before submitting.
