# Code Analyst Agent - Demo Script

## Introduction (15 seconds)

"Hi! I'm demonstrating the Code Analyst Agent - a production-ready multi-agent system built with Google's ADK that performs comprehensive codebase analysis using Gemini 2.5 Pro and BigQuery."

## Problem Statement (20 seconds)

"Development teams struggle with:

- Hidden security vulnerabilities
- Performance bottlenecks in large codebases  
- Manual code reviews that miss critical issues
- Lack of automated architectural insights

Our solution automates this with AI-powered multi-agent analysis."

## Architecture Overview (30 seconds)

*Show architecture diagram*

"The system uses:

- Google ADK for multi-agent orchestration
- Specialized agents for parsing, security, and performance
- Gemini 2.5 Pro for deep code understanding
- BigQuery for CVE vulnerability analysis
- Multiple output formats for different stakeholders"

## Live Demo (90 seconds)

### 1. CLI Demo (30 seconds)

```bash
# Analyze a GitHub repository
codebase-analyze --repo https://github.com/tensorflow/models --output tf_analysis --formats json,html,pdf

# Show real-time progress
```

### 2. Web UI Demo (30 seconds)

- Navigate to deployed Cloud Run URL
- Enter repository URL
- Show interactive analysis
- Download generated reports

### 3. Results Walkthrough (30 seconds)

- Open HTML report
- Show security vulnerabilities detected
- Highlight performance issues found
- Display Gemini's architectural insights
- Show actionable recommendations

## Technical Implementation (20 seconds)

"Built with:

- Python multi-agent architecture
- Flask REST API with rate limiting
- Docker containers with security hardening
- Cloud Run auto-scaling deployment
- Comprehensive test coverage (70%+)"

## Use Cases & Impact (15 seconds)

"Perfect for:

- Pre-deployment security audits
- Performance optimization planning
- Technical debt assessment
- Automated code quality gates in CI/CD"

## Closing (10 seconds)

"The Code Analyst Agent transforms how teams understand and improve their codebases - making secure, performant software easier to build. Thank you!"

---

## Demo Commands Reference

### Setup

```bash
# Clone and setup
git clone https://github.com/your-org/codebase-analysis
cd codebase-analysis
pip install -e .

# Configure credentials
export GOOGLE_API_KEY=your_key
export NVD_API_KEY=your_nvd_key
```

### Run Analysis

```bash
# Local repository
codebase-analyze --repo ./my-project --output analysis

# Remote repository  
codebase-analyze --repo https://github.com/user/repo --formats json,html,pdf

# Using ADK
adk run codebase_analysis.adk_agent
```

### API Usage

```bash
# Start API server
python -m codebase_analysis.api

# Make API request
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo"}'
```
