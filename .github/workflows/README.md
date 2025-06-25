# CI/CD Configuration

This directory contains the CI/CD pipeline configuration for the Code Analyst Agent project.

## Required GitHub Secrets

To run the CI/CD pipeline successfully, you need to configure the following secrets in your GitHub repository settings:

### 1. `GCP_PROJECT_ID`

- **Description**: Your Google Cloud Project ID
- **Example**: `my-gcp-project-123`
- **Required for**: Building and pushing Docker images to Google Container Registry (GCR)

### 2. `GCP_SA_KEY`

- **Description**: Service Account JSON key with the following permissions:
  - Container Registry Admin
  - Cloud Run Admin
  - Service Account User
- **How to create**:
  1. Go to [Google Cloud Console](https://console.cloud.google.com)
  2. Navigate to IAM & Admin > Service Accounts
  3. Create a new service account or use an existing one
  4. Add the required roles
  5. Create a JSON key
  6. Copy the entire JSON content as the secret value

## Pipeline Jobs

### 1. Test Job

- Runs on Python 3.11
- Executes linting with ruff
- Runs pytest with coverage
- Uploads coverage to Codecov

### 2. Security Scan Job

- Runs Bandit for Python security vulnerabilities
- Runs Safety scan for dependency vulnerabilities
- Uses the new `safety scan` command instead of deprecated `check`

### 3. Build Job

- Builds Docker image
- Pushes to Google Container Registry
- Only runs on push to main/develop or on release

### 4. Deploy Staging Job

- Deploys to Cloud Run staging environment
- Only runs on push to develop branch

### 5. Deploy Production Job

- Deploys to Cloud Run production environment
- Only runs on release events

### 6. Security Monitoring Job

- Runs Trivy vulnerability scanner on the built image
- Uploads results to GitHub Security tab
- Only runs on push to main branch when GCP_PROJECT_ID is set

## Troubleshooting

### Trivy Scanner Fails

If you see an error like `gcr.io//codebase-analysis:main`, it means the `GCP_PROJECT_ID` secret is not set. The pipeline will skip the Trivy scan with a warning.

### Safety Check Fails

The pipeline is configured to warn on vulnerabilities but not fail the build. Review the Safety output for any critical vulnerabilities that need immediate attention.

### Permission Errors

Ensure your service account has all the required permissions listed above. You can test locally with:

```bash
gcloud auth activate-service-account --key-file=path/to/key.json
gcloud auth configure-docker
```
