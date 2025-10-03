# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 1. OpenAI Module Error

**Error Message:**
```
ModuleNotFoundError: No module named 'openai'
```

**Cause:** The application has optional AI features that require the `openai` package, but it's not included in the basic requirements.

**Solutions:**

#### Option A: Install OpenAI (Recommended)
```bash
source venv/bin/activate
pip install openai
```

#### Option B: Make AI Features Optional (Quick Fix)
Edit `app.py` and comment out the AI import:
```python
# from ai_sprint_insights import AISprintInsights
```

#### Option C: Use Compatible Requirements
The `requirements_local.txt` file excludes problematic dependencies. Use it instead:
```bash
pip install -r requirements_local.txt
```

### 2. Python Version Compatibility

**Error Message:**
```
No matching distribution found for requests>=2.31.0
```

**Cause:** Your Python version (3.6.8) is older and doesn't support newer package versions.

**Solution:**
Use the compatible requirements file:
```bash
pip install -r requirements_local.txt
```

### 3. Port Already in Use

**Error Message:**
```
Address already in use
```

**Solution:**
```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process (replace <PID> with actual process ID)
kill -9 <PID>

# Or use a different port by modifying app.py
```

### 4. Jira Connection Issues

**Error Message:**
```
Failed to fetch labels from Jira
```

**Cause:** Jira credentials not configured.

**Solutions:**

#### Option A: Environment Variables
Create `.env` file:
```bash
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
```

#### Option B: Web Interface
1. Go to `http://localhost:8080/settings`
2. Enter your Jira credentials
3. Test the connection

### 5. Node.js Issues (Frontend Development)

**Error Message:**
```
Unsupported URL Type: npm:string-width@^4.2.0
```

**Cause:** Node.js version too old (v6.16.0).

**Solutions:**

#### Option A: Use Pre-built Frontend (Current Setup)
The application already has a built React frontend, so Node.js issues don't affect basic functionality.

#### Option B: Update Node.js (For Development)
```bash
# Install Node Version Manager
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18
nvm use 18
```

## Quick Fixes

### Reset Everything
```bash
# Remove virtual environment
rm -rf venv

# Recreate and reinstall
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_local.txt
```

### Check Server Status
```bash
# Test if server is running
curl http://localhost:8080/

# Check what's using port 8080
netstat -tlnp | grep 8080
```

### Debug Mode
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 app.py
```

## Environment-Specific Notes

### CentOS/RHEL 7 (Your System)
- Python 3.6.8 is available but limited
- Node.js v6.16.0 is very old
- Use compatible package versions
- Consider using Docker for development if issues persist

### Alternative: Docker Development
If local setup continues to have issues:
```bash
# Use Docker for development
docker-compose -f docker-compose.dev.yml up --build
```

## Getting Help

1. **Check Logs**: Look at the terminal output for error messages
2. **Verify Setup**: Run `./start_local.sh` for automated setup
3. **Test Endpoints**: Use `curl` to test API endpoints
4. **Check Dependencies**: Ensure all packages are installed correctly

## Success Indicators

✅ **Server Running**: `curl http://localhost:8080/` returns HTML
✅ **API Working**: `curl http://localhost:8080/api/settings/load-jira` returns JSON
✅ **No Errors**: Terminal shows "Running on http://0.0.0.0:8080"
✅ **Frontend Loads**: Browser shows the React application interface
