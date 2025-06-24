# 🚀 Sharing Docker Images for Hosting - Complete Guide

## 📋 Overview
This guide covers all the methods to share your Jira Hub Docker image for hosting and deployment across different platforms and environments.

---

## 🌐 Method 1: Docker Hub (Recommended for Public Projects)

### 📝 Setup Docker Hub Account
1. Create account at [hub.docker.com](https://hub.docker.com)
2. Login from terminal: `docker login`

### 🏗️ Build and Push to Docker Hub
```bash
# Build image with your Docker Hub username
docker build -t yourusername/jira-hub:latest .

# Tag with version (optional)
docker tag yourusername/jira-hub:latest yourusername/jira-hub:v1.0

# Push to Docker Hub
docker push yourusername/jira-hub:latest
docker push yourusername/jira-hub:v1.0
```

### 📥 Others Can Pull Your Image
```bash
# Pull and run your image
docker pull yourusername/jira-hub:latest
docker run -d --name jira-hub -p 8080:8080 --env-file .env yourusername/jira-hub:latest
```

### 🔒 Private Repository on Docker Hub
```bash
# Create private repo on Docker Hub, then:
docker build -t yourusername/jira-hub-private:latest .
docker push yourusername/jira-hub-private:latest

# Others need to login to pull private images
docker login
docker pull yourusername/jira-hub-private:latest
```

---

## ☁️ Method 2: Cloud Container Registries

### 🔶 AWS Elastic Container Registry (ECR)
```bash
# Install AWS CLI and configure credentials
aws configure

# Create ECR repository
aws ecr create-repository --repository-name jira-hub --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789012.dkr.ecr.us-east-1.amazonaws.com

# Build and tag for ECR
docker build -t jira-hub .
docker tag jira-hub:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/jira-hub:latest

# Push to ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/jira-hub:latest
```

### 🟦 Google Container Registry (GCR)
```bash
# Install Google Cloud SDK and authenticate
gcloud auth configure-docker

# Build and tag for GCR
docker build -t jira-hub .
docker tag jira-hub gcr.io/YOUR_PROJECT_ID/jira-hub:latest

# Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/jira-hub:latest
```

### 🟦 Azure Container Registry (ACR)
```bash
# Login to Azure and ACR
az login
az acr login --name myregistry

# Build and tag for ACR
docker build -t jira-hub .
docker tag jira-hub myregistry.azurecr.io/jira-hub:latest

# Push to ACR
docker push myregistry.azurecr.io/jira-hub:latest
```

---

## 🐙 Method 3: GitHub Container Registry (GHCR)

### 🔧 Setup GitHub Container Registry
```bash
# Create Personal Access Token with packages:write permission
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Build and tag for GHCR
docker build -t jira-hub .
docker tag jira-hub ghcr.io/yourusername/jira-hub:latest

# Push to GHCR
docker push ghcr.io/yourusername/jira-hub:latest
```

### 📦 GitHub Actions for Automatic Building
Create `.github/workflows/docker-publish.yml`:
```yaml
name: Docker Build and Push

on:
  push:
    branches: [ main ]
    tags: [ 'v*' ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Login to GitHub Container Registry
      uses: docker/login-action@v2
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        push: true
        tags: |
          ghcr.io/${{ github.repository }}:latest
          ghcr.io/${{ github.repository }}:${{ github.sha }}
```

---

## 💾 Method 4: Save/Load Docker Images as Files

### 📤 Export Image to File
```bash
# Save image to tar file
docker save -o jira-hub.tar jira-hub:latest

# Compress for smaller size
docker save jira-hub:latest | gzip > jira-hub.tar.gz
```

### 📥 Import Image from File
```bash
# Load image from tar file
docker load -i jira-hub.tar

# Load compressed image
gunzip -c jira-hub.tar.gz | docker load
```

### 📁 Share via Cloud Storage
```bash
# Upload to cloud storage (AWS S3 example)
aws s3 cp jira-hub.tar.gz s3://your-bucket/docker-images/

# Others can download and load
aws s3 cp s3://your-bucket/docker-images/jira-hub.tar.gz .
gunzip -c jira-hub.tar.gz | docker load
```

---

## 🏢 Method 5: Private Container Registry

### 🔧 Setup Private Registry with Docker
```bash
# Run private registry
docker run -d -p 5000:5000 --name registry registry:2

# Tag for private registry
docker tag jira-hub:latest localhost:5000/jira-hub:latest

# Push to private registry
docker push localhost:5000/jira-hub:latest

# Pull from private registry
docker pull localhost:5000/jira-hub:latest
```

### 🔒 Secure Private Registry
```bash
# With authentication and SSL
docker run -d \
  -p 5000:5000 \
  --name registry \
  -v /path/to/certs:/certs \
  -v /path/to/auth:/auth \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/domain.crt \
  -e REGISTRY_HTTP_TLS_PRIVATE_KEY=/certs/domain.key \
  -e REGISTRY_AUTH=htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  registry:2
```

---

## 🌍 Method 6: Cloud Platform Deployment

### 🚀 Deploy to Cloud Platforms

#### AWS ECS/Fargate
```bash
# Push to ECR (see Method 2)
# Create ECS task definition referencing your ECR image
# Deploy to ECS cluster or Fargate
```

#### Google Cloud Run
```bash
# Push to GCR (see Method 2)
gcloud run deploy jira-hub \
  --image gcr.io/YOUR_PROJECT_ID/jira-hub:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Azure Container Instances
```bash
# Push to ACR (see Method 2)
az container create \
  --resource-group myResourceGroup \
  --name jira-hub \
  --image myregistry.azurecr.io/jira-hub:latest \
  --cpu 1 --memory 1 \
  --registry-login-server myregistry.azurecr.io \
  --registry-username myregistry \
  --registry-password myPassword \
  --dns-name-label jira-hub-unique \
  --ports 8080
```

#### DigitalOcean App Platform
```yaml
# app.yaml
name: jira-hub
services:
- name: web
  source_dir: /
  github:
    repo: your-username/jira-hub
    branch: main
  run_command: python app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: JIRA_URL
    value: https://your-company.atlassian.net
  - key: JIRA_EMAIL
    value: your-email@company.com
  - key: JIRA_API_TOKEN
    value: your-token
    type: SECRET
```

---

## 📋 Quick Reference Commands

### 🏗️ Build and Tag for Different Registries
```bash
# Docker Hub
docker build -t yourusername/jira-hub:latest .

# AWS ECR
docker build -t 123456789012.dkr.ecr.us-east-1.amazonaws.com/jira-hub:latest .

# Google GCR
docker build -t gcr.io/PROJECT_ID/jira-hub:latest .

# Azure ACR
docker build -t myregistry.azurecr.io/jira-hub:latest .

# GitHub GHCR
docker build -t ghcr.io/username/jira-hub:latest .
```

### 📤 Push Commands
```bash
# Docker Hub
docker push yourusername/jira-hub:latest

# AWS ECR
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/jira-hub:latest

# Google GCR
docker push gcr.io/PROJECT_ID/jira-hub:latest

# Azure ACR
docker push myregistry.azurecr.io/jira-hub:latest

# GitHub GHCR
docker push ghcr.io/username/jira-hub:latest
```

---

## 🎯 Recommendations by Use Case

### 🔓 Public Open Source Project
- **Best Choice**: Docker Hub (free public repositories)
- **Alternative**: GitHub Container Registry

### 🔒 Private/Commercial Project
- **Best Choice**: Cloud provider registry (AWS ECR, Google GCR, Azure ACR)
- **Alternative**: Docker Hub private repository, GitHub Container Registry

### 🏢 Enterprise/Internal Use
- **Best Choice**: Private container registry
- **Alternative**: Cloud provider registry with VPC

### 💡 Development/Testing
- **Best Choice**: Save/load as files
- **Alternative**: Local private registry

---

## ⚡ Quick Start Examples

### 🐳 Share via Docker Hub (Public)
```bash
# 1. Build and push
docker build -t yourusername/jira-hub:latest .
docker push yourusername/jira-hub:latest

# 2. Share this command with others:
docker run -d --name jira-hub -p 8080:8080 --env-file .env yourusername/jira-hub:latest
```

### 💾 Share via File (No Registry)
```bash
# 1. Save to file
docker save jira-hub:latest | gzip > jira-hub.tar.gz

# 2. Share file, others load with:
gunzip -c jira-hub.tar.gz | docker load
docker run -d --name jira-hub -p 8080:8080 --env-file .env jira-hub:latest
```

### ☁️ Deploy to Cloud Run (Google Cloud)
```bash
# 1. Push to GCR
docker build -t gcr.io/PROJECT_ID/jira-hub:latest .
docker push gcr.io/PROJECT_ID/jira-hub:latest

# 2. Deploy to Cloud Run
gcloud run deploy jira-hub --image gcr.io/PROJECT_ID/jira-hub:latest --platform managed
```

---

## 🔐 Security Best Practices

1. **Use Private Registries** for commercial/sensitive applications
2. **Scan Images** for vulnerabilities before sharing
3. **Use Specific Tags** instead of 'latest' for production
4. **Set Up Authentication** for registry access
5. **Regular Updates** - rebuild and push updates regularly
6. **Environment Variables** - never bake secrets into images
7. **Multi-stage Builds** - keep production images minimal

---

## 📞 Support & Resources

- **Docker Hub**: [hub.docker.com](https://hub.docker.com)
- **AWS ECR**: [AWS ECR Documentation](https://docs.aws.amazon.com/ecr/)
- **Google GCR**: [GCR Documentation](https://cloud.google.com/container-registry)
- **Azure ACR**: [ACR Documentation](https://docs.microsoft.com/en-us/azure/container-registry/)
- **GitHub GHCR**: [GHCR Documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)

Your Jira Hub application is now ready to be shared and deployed anywhere! 🚀🌍 