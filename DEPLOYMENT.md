# 🚀 Production Deployment Guide

This guide covers deploying the Code Analyst Agent to production environments including Google Cloud Run, Kubernetes, and on-premises deployments.

## 📋 Prerequisites

- Google Cloud Platform account with billing enabled
- Docker installed
- `gcloud` CLI installed and authenticated
- `kubectl` configured (for Kubernetes deployments)
- Domain name (optional, for custom domains)

## 🔧 Configuration

### 1. Environment Setup

Create production environment variables:

```bash
# Copy the template
cp .env.example .env.prod

# Edit with production values
nano .env.prod
```

**Required Configuration:**

```bash
# Google Cloud
GOOGLE_CLOUD_PROJECT=your-production-project-id
GOOGLE_APPLICATION_CREDENTIALS=/var/secrets/google/key.json

# Or use API key for simpler setup
GOOGLE_API_KEY=your-production-api-key

# Security
NVD_API_KEY=your-nvd-api-key-here
SECRET_KEY=your-super-secure-random-secret-key

# Logging
LOG_FORMAT=json
LOG_LEVEL=INFO

# Production settings
FLASK_ENV=production
DEBUG=false
```

### 2. Create GCP Secrets

```bash
# Create secrets for sensitive data
gcloud secrets create codebase-analysis-secrets \
  --data-file=production-secrets.json

# Example secrets.json:
{
  "GOOGLE_API_KEY": "your-api-key",
  "NVD_API_KEY": "your-nvd-key",
  "SECRET_KEY": "your-flask-secret"
}
```

## 🐳 Docker Deployment

### Build Production Image

```bash
# Build optimized production image
docker build -t gcr.io/PROJECT_ID/codebase-analysis:latest .

# Push to Google Container Registry
docker push gcr.io/PROJECT_ID/codebase-analysis:latest
```

### Local Docker Testing

```bash
# Run with production configuration
docker run -d \
  --name codebase-analysis \
  -p 8000:8000 \
  -e GOOGLE_API_KEY=your-key \
  -e NVD_API_KEY=your-nvd-key \
  -e LOG_FORMAT=json \
  -e FLASK_ENV=production \
  -v /path/to/reports:/mnt/reports \
  gcr.io/PROJECT_ID/codebase-analysis:latest

# Check logs
docker logs codebase-analysis

# Test health endpoint
curl http://localhost:8000/healthz
```

## ☁️ Google Cloud Run Deployment

### Automated Deployment

```bash
# Deploy using provided configuration
gcloud run services replace cloud-run-config.yaml --region=us-central1

# Or use CLI
gcloud run deploy codebase-analysis \
  --image=gcr.io/PROJECT_ID/codebase-analysis:latest \
  --platform=managed \
  --region=us-central1 \
  --allow-unauthenticated \
  --memory=2Gi \
  --cpu=2 \
  --max-instances=10 \
  --min-instances=1 \
  --set-env-vars="FLASK_ENV=production,LOG_FORMAT=json" \
  --set-secrets="GOOGLE_API_KEY=codebase-analysis-secrets:latest:GOOGLE_API_KEY,NVD_API_KEY=codebase-analysis-secrets:latest:NVD_API_KEY"
```

### Custom Domain Setup

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service=codebase-analysis \
  --domain=analyzer.yourdomain.com \
  --region=us-central1
```

### Cloud Run Monitoring

```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=codebase-analysis" --limit 50

# Monitor metrics
gcloud monitoring dashboards list
```

## ⚡ Kubernetes Deployment

### 1. Prepare Secrets

```bash
# Create namespace
kubectl create namespace codebase-analysis

# Create secrets
kubectl create secret generic codebase-analysis-secrets \
  --from-literal=GOOGLE_API_KEY=your-api-key \
  --from-literal=NVD_API_KEY=your-nvd-key \
  --from-literal=SECRET_KEY=your-flask-secret \
  --namespace=codebase-analysis

# Create service account secret
kubectl create secret generic gcp-service-account \
  --from-file=key.json=path/to/service-account.json \
  --namespace=codebase-analysis
```

### 2. Deploy Application

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s-deployment.yaml -n codebase-analysis

# Check deployment status
kubectl get pods -n codebase-analysis
kubectl get services -n codebase-analysis

# View logs
kubectl logs -f deployment/codebase-analysis -n codebase-analysis
```

### 3. Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: codebase-analysis-ingress
  namespace: codebase-analysis
  annotations:
    kubernetes.io/ingress.class: "gce"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    kubernetes.io/ingress.global-static-ip-name: "codebase-analysis-ip"
spec:
  tls:
  - hosts:
    - analyzer.yourdomain.com
    secretName: codebase-analysis-tls
  rules:
  - host: analyzer.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: codebase-analysis-service
            port:
              number: 80
```

### 4. Horizontal Pod Autoscaling

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: codebase-analysis-hpa
  namespace: codebase-analysis
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: codebase-analysis
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## 📊 Monitoring & Observability

### 1. Google Cloud Monitoring

```bash
# Create alerting policy
gcloud alpha monitoring policies create --policy-from-file=monitoring-policy.yaml
```

### 2. Application Monitoring

```yaml
# monitoring-policy.yaml
displayName: "Codebase Analysis Service Health"
conditions:
  - displayName: "High Error Rate"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="codebase-analysis"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 0.05
      duration: 300s
  - displayName: "High Response Time"
    conditionThreshold:
      filter: 'resource.type="cloud_run_revision" AND resource.labels.service_name="codebase-analysis"'
      comparison: COMPARISON_GREATER_THAN
      thresholdValue: 5000
      duration: 300s
```

### 3. Custom Metrics

```python
# Add to your Flask app
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

## 🔒 Security Configuration

### 1. Network Security

```bash
# Create firewall rules (GKE)
gcloud compute firewall-rules create allow-codebase-analysis \
  --allow tcp:8000 \
  --source-ranges 10.0.0.0/8 \
  --description "Allow internal access to codebase analysis"
```

### 2. IAM Configuration

```bash
# Create service account with minimal permissions
gcloud iam service-accounts create codebase-analysis-sa \
  --display-name="Codebase Analysis Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:codebase-analysis-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:codebase-analysis-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### 3. Security Scanning

```bash
# Run security scan on deployed image
gcloud container images scan IMAGE_URL

# Use Cloud Security Command Center
gcloud scc findings list \
  --organization=ORGANIZATION_ID \
  --filter="category=\"VULNERABILITY\""
```

## 🔄 CI/CD Integration

### GitHub Actions Deployment

The included `.github/workflows/ci-cd.yml` provides:

- **Automated Testing**: Multi-Python version testing
- **Security Scanning**: Bandit and Trivy scans
- **Image Building**: Docker image builds and pushes
- **Staging Deployment**: Automatic deployment to staging
- **Production Deployment**: Triggered by releases

### Manual Production Release

```bash
# Create and push a release tag
git tag -a v1.0.0 -m "Production release v1.0.0"
git push origin v1.0.0

# This triggers the production deployment workflow
```

## 📈 Scaling Considerations

### Cloud Run Scaling

- **Memory**: Start with 2Gi, monitor usage
- **CPU**: 2 vCPUs recommended for large repositories
- **Concurrency**: Set to 80 for optimal throughput
- **Max Instances**: Set based on expected load

### Kubernetes Scaling

- **Resource Requests**: Set conservative requests
- **Resource Limits**: Set appropriate limits
- **HPA**: Configure based on CPU/memory metrics
- **Cluster Autoscaling**: Enable for cost optimization

## 🔧 Troubleshooting

### Common Issues

1. **High Memory Usage**

   ```bash
   # Check memory usage
   kubectl top pods -n codebase-analysis
   
   # Increase memory limits
   kubectl patch deployment codebase-analysis -n codebase-analysis -p '{"spec":{"template":{"spec":{"containers":[{"name":"codebase-analysis","resources":{"limits":{"memory":"4Gi"}}}]}}}}'
   ```

2. **API Rate Limits**

   ```bash
   # Check logs for rate limit errors
   kubectl logs deployment/codebase-analysis -n codebase-analysis | grep "rate limit"
   
   # Adjust request intervals or implement backoff
   ```

3. **BigQuery Connection Issues**

   ```bash
   # Verify service account permissions
   gcloud auth list
   gcloud auth activate-service-account --key-file=service-account.json
   ```

### Health Checks

```bash
# Cloud Run health check
curl https://your-service-url/healthz

# Kubernetes health check
kubectl get pods -n codebase-analysis
kubectl describe pod POD_NAME -n codebase-analysis
```

### Log Analysis

```bash
# Stream logs in real-time
gcloud logs tail "resource.type=cloud_run_revision AND resource.labels.service_name=codebase-analysis"

# Search for specific errors
gcloud logs read 'resource.type=cloud_run_revision AND jsonPayload.severity="ERROR"' --limit=50
```

## 📊 Performance Optimization

### Database Optimization

```sql
-- BigQuery optimization
CREATE OR REPLACE TABLE `project.security_analytics.vulnerabilities_optimized`
PARTITION BY DATE(discovery_date)
CLUSTER BY package_name
AS SELECT * FROM `project.security_analytics.vulnerabilities`;
```

### Caching Strategy

```python
# Redis caching for frequent queries
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://redis-service:6379/0',
    'CACHE_DEFAULT_TIMEOUT': 3600
}
```

## 🎯 Production Checklist

- [ ] Environment variables configured
- [ ] Secrets created and secured
- [ ] Health checks working
- [ ] Monitoring and alerting set up
- [ ] Security scanning completed
- [ ] Performance testing completed
- [ ] Backup and disaster recovery planned
- [ ] Documentation updated
- [ ] Team access and permissions configured
- [ ] Load testing completed

## 📞 Support

For production support issues:

1. **Check logs first**: Use the logging commands above
2. **Review monitoring**: Check Google Cloud Monitoring dashboards
3. **Open GitHub Issue**: For bugs or feature requests
4. **Emergency Contact**: [Your emergency contact process]

---

**Note**: Replace `PROJECT_ID`, `yourdomain.com`, and other placeholders with your actual values before deployment.
