# 📄 Code Analyst Agent — Full PRD

## ✅ 1. Project Overview

**Title:** Code Analyst Agent using Gemini 2.5 Pro and Google ADK  
**Goal:** Develop a robust Python multi-agent system that analyzes large software codebases, orchestrated via Google’s ADK, using Gemini 2.5 Pro for deep, context-rich understanding, producing actionable security, performance, and architectural insights.

## ✅ 2. Target Users

- Tech Leads & Architects — understand code structure & risks
- Security Engineers — detect CVEs, code vulnerabilities
- Performance Engineers — identify bottlenecks, inefficiencies

## ✅ 3. Use Cases

- Analyze large monolithic or microservice repos
- Spot security vulnerabilities
- Map module dependencies and architecture
- Highlight performance risks
- Generate easy-to-share JSON & HTML reports

## ✅ 4. Functional Requirements

| ID | Feature | Description |
|----|---------|--------------|
| F1 | **Codebase Ingestion** | Accept GitHub URL/local path; clone or load recursively |
| F2 | **Orchestrator Agent** | Manage sub-agents, maintain context, merge outputs |
| F3 | **Parser Agent** | Use `CodeUnderstandingTool` to parse files, build ASTs, call graphs |
| F4 | **Security Agent** | Use `BigQueryTool` or CVE feed to find vulnerabilities |
| F5 | **Performance Agent** | Detect nested loops, large files, high complexity |
| F6 | **Gemini 2.5 Pro** | Use large context window for whole-project insights |
| F7 | **Report Generator** | JSON + HTML with Jinja2 templates |
| F8 | **CLI & Flask API** | Command line tool + Cloud Run-ready Flask wrapper |
| F9 | **Logging & Testing** | Clear logs, unit tests for each agent |

## ✅ 5. Non-Functional Requirements

- Must handle repos up to 500,000 LOC
- Complete analysis in ~10 min for 100k LOC
- Runs on Vertex AI, Cloud Run, GKE
- Secure: no code stored post-analysis
- Well-documented with README & docstrings

## ✅ 6. Architecture

**Agents:** Orchestrator → Parser, Security, Performance → Report Generator  
**Tools:** CodeUnderstandingTool, BigQueryTool  
**Data Flow:** Repo → AST & call graphs → CVE check → Performance scan → Aggregated report

## ✅ 7. APIs & CLI

**Input JSON:** `{ "repo_url": "...", "output": "report.json" }`  
**Output JSON:** `{ "metadata": {...}, "parser_results": {...}, "security_findings": [...], "performance_issues": [...], "recommendations": [...] }`  
**CLI:** `codebase-analyze --repo <URL> --output report.json`  
**Flask:** `POST /analyze` with JSON payload

## ✅ 8. Workflows

1. Orchestrator clones repo
2. Parser Agent parses, builds AST
3. Security Agent queries CVE DB
4. Performance Agent scans for inefficiencies
5. Orchestrator merges results
6. Report Generator outputs JSON + HTML

## ✅ 9. Acceptance Criteria

- Handles 10,000+ LOC repos
- Detects known CVEs in test repo
- Finds at least 2 performance issues
- Passes unit tests
- Produces valid JSON & HTML reports

## ✅ 10. Packaging & Deployment

- Python package with `setup.py` & `pyproject.toml`
- Dockerfile & .dockerignore for container builds
- Cloud Run deployment with Flask wrapper & gunicorn
- Optional GKE YAML for clusters
- CI/CD GitHub Actions pipeline (optional)

## ✅ 11. Next Steps

- Integrate tools into agents
- Test locally & in Vertex AI Workbench
- Containerize and deploy to Cloud Run
- Document with README & usage examples

---
This PRD is ready for direct code generation and deployment. 🚀
