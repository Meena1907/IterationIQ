# Deployment Steps Guide

## 🚀 Quick Deployment Process

This guide outlines the steps to stop the current container, pull the latest changes from master, and rebuild/deploy the application.

---

## 📋 Prerequisites
- Docker and Docker Compose installed
- Git repository cloned locally
- Access to the remote repository

---

## 🔄 Deployment Steps

### 1. Stop Current Container
```bash
# Stop and remove the current running containers
docker-compose down
```

### 2. Pull Latest Changes from Master
```bash
# Fetch the latest changes from remote repository
git fetch origin

# Pull the latest changes from master branch
git pull origin master
```

### 3. Rebuild Docker Image
```bash
# Build the Docker image with latest changes (no cache)
docker-compose build --no-cache
```

### 4. Deploy the Application
```bash
# Start the application in detached mode
docker-compose up -d
```

### 5. Verify Deployment
```bash
# Check if container is running
docker-compose ps

# Check application logs
docker-compose logs --tail=20

# Test the application (optional)
curl http://localhost:8080
```

---

## 🚨 Alternative: Force Pull (if needed)

If you encounter merge conflicts or want to completely reset to remote:

```bash
# Stop containers
docker-compose down

# Reset to remote master (WARNING: This will discard local changes)
git fetch origin
git reset --hard origin/master

# Rebuild and deploy
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔧 Troubleshooting

### If container fails to start:
```bash
# Check detailed logs
docker-compose logs

# Check container status
docker-compose ps -a

# Restart container
docker-compose restart
```

### If build fails:
```bash
# Clean up Docker cache
docker system prune -f

# Rebuild without cache
docker-compose build --no-cache
```

### If port is already in use:
```bash
# Check what's using port 8080
lsof -i :8080

# Kill the process if needed
sudo kill -9 <PID>
```

---

## 📝 Quick One-Liner (for experienced users)

```bash
docker-compose down && git pull origin master && docker-compose build --no-cache && docker-compose up -d
```

---

## 🌐 Access the Application

After successful deployment, access the application at:
- **Local**: http://localhost:8080
- **Network**: http://<your-server-ip>:8080

---

## 📊 Monitor Application

```bash
# View real-time logs
docker-compose logs -f

# Check resource usage
docker stats

# View container details
docker-compose ps
```

---

## 🔄 Rollback (if needed)

If you need to rollback to a previous version:

```bash
# Stop current containers
docker-compose down

# Check git log for previous commits
git log --oneline -10

# Reset to previous commit
git reset --hard <commit-hash>

# Rebuild and deploy
docker-compose build --no-cache
docker-compose up -d
```

---

*Last updated: $(date)*
*Repository: git@galaxy.corp.thoughtspot.com:dev/Jira_report_tpm.git* 