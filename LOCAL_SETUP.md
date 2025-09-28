# 🚀 Local Development Setup Guide

This guide provides step-by-step instructions to run the Jira TPM application locally for debugging and testing without Docker.

## 📋 Prerequisites

- **Python**: 3.6+ (tested with Python 3.6.8)
- **Node.js**: Not required for basic setup (uses pre-built frontend)
- **Git**: For cloning the repository
- **Jira Access**: Valid Jira Cloud instance with API token

## 🛠️ Setup Instructions

### 1. Navigate to Project Directory
```bash
cd /home/hudson/jira_tpm
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv venv
```

### 3. Activate Virtual Environment
```bash
source venv/bin/activate
```

### 4. Upgrade pip (Important for older Python versions)
```bash
pip install --upgrade pip
```

### 5. Install Python Dependencies
```bash
# Install compatible versions for Python 3.6
pip install -r requirements_local.txt
```

**Note**: The `requirements_local.txt` file contains versions compatible with Python 3.6:
```
flask==2.0.1
requests>=2.25.0,<2.31.0
python-dotenv==0.19.0
flask-cors==3.0.10
werkzeug==2.0.1
python-dateutil>=2.8.2
cryptography>=3.4.8
```

### 6. Configure Environment Variables (Optional)
Create a `.env` file in the project root:
```bash
# Optional: Set Jira credentials via environment variables
JIRA_URL=https://your-company.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=your-api-token-here
```

**Alternative**: Configure Jira credentials through the web interface at `http://localhost:8080/settings`

### 7. Start the Application
```bash
python3 app.py
```

## 🌐 Access the Application

- **URL**: `http://localhost:8080`
- **Frontend**: React application (pre-built)
- **Backend**: Flask API server
- **Port**: 8080 (not the typical Flask 5000)

## 🔧 Development Workflow

### Backend Development
1. **Edit Python files** in the project root
2. **Restart Flask server** after changes:
   ```bash
   # Stop current server (Ctrl+C)
   # Then restart:
   source venv/bin/activate
   python3 app.py
   ```

### Frontend Development
- **Current Setup**: Uses pre-built React application
- **For React Development**: Would require Node.js 14+ and npm 6+
- **Alternative**: Edit React files and rebuild (requires Node.js setup)

### API Testing
Test endpoints using curl:
```bash
# Test main application
curl http://localhost:8080/

# Test API endpoints
curl http://localhost:8080/api/labels
curl http://localhost:8080/api/settings/load-jira
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Module Import Errors
**Error**: `ModuleNotFoundError: No module named 'openai'`
**Solution**: The application has optional AI features. If you encounter this error:
```bash
# Install missing dependencies (if needed)
pip install openai
# Or modify the code to make AI features optional
```

#### 2. Python Version Compatibility
**Error**: `No matching distribution found for requests>=2.31.0`
**Solution**: Use the compatible requirements file:
```bash
pip install -r requirements_local.txt
```

#### 3. Port Already in Use
**Error**: `Address already in use`
**Solution**: 
```bash
# Find process using port 8080
lsof -i :8080
# Kill the process
kill -9 <PID>
```

#### 4. Jira Connection Issues
**Error**: `Failed to fetch labels from Jira`
**Solution**: Configure Jira credentials:
1. Go to `http://localhost:8080/settings`
2. Enter your Jira URL, email, and API token
3. Test the connection

### Debug Mode
Enable detailed logging:
```bash
export FLASK_ENV=development
export FLASK_DEBUG=1
python3 app.py
```

## 📁 Project Structure

```
jira_tpm/
├── app.py                          # Main Flask application
├── requirements_local.txt           # Compatible Python dependencies
├── venv/                           # Python virtual environment
├── frontend/                       # React frontend (pre-built)
│   ├── src/                        # React source code
│   ├── public/                     # Static assets
│   └── build/                      # Built React app (served by Flask)
├── scripts/                        # Core business logic
├── templates/                      # Flask templates
└── .env                           # Environment variables (optional)
```

## 🔄 Quick Start Commands

### Start Development Server
```bash
cd /home/hudson/jira_tpm
source venv/bin/activate
python3 app.py
```

### Stop Server
```bash
# Press Ctrl+C in the terminal running the server
```

### Restart After Changes
```bash
# Stop server (Ctrl+C)
source venv/bin/activate
python3 app.py
```

### Check Server Status
```bash
# Check if server is running
curl http://localhost:8080/
# Should return HTML content
```

## 🎯 Key Features Available

- **Sprint Analytics**: Comprehensive sprint reporting
- **Capacity Planning**: Individual performance analysis
- **Label Management**: Advanced label operations
- **Settings**: Jira configuration management
- **Export Options**: CSV, PDF, shareable reports

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify Python version: `python3 --version`
3. Ensure virtual environment is activated: `which python`
4. Check server logs for error messages

## 🚀 Next Steps

1. **Configure Jira**: Set up your Jira credentials in the Settings page
2. **Test Features**: Explore sprint analytics and capacity planning
3. **Customize**: Modify the code for your specific needs
4. **Deploy**: Use Docker for production deployment

---

**Last Updated**: January 2025
**Compatible With**: Python 3.6+, Flask 2.0+, React 18+
