# 📁 Project Structure

## 🏗️ **Organized Project Layout**

```
jira_tpm/
├── 📁 backend/                    # Python Flask backend
│   ├── app.py                    # Main Flask application
│   ├── app_modified.py           # Modified version of app
│   ├── ai_sprint_insights.py     # AI insights functionality
│   ├── add_org_analytics.py      # Organization analytics
│   ├── settings_manager.py       # Settings management
│   ├── user_tracking.py          # User tracking functionality
│   └── 📁 scripts/               # Python utility scripts
│       ├── jira_sprint_report.py
│       └── user_capacity_analysis.py
│
├── 📁 frontend/                   # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   └── utils/
│   └── package.json
│
├── 📁 config/                     # Configuration files
│   ├── set_jira_creds.sh         # JIRA credentials setup
│   ├── start_local.sh            # Local startup script
│   └── build-docker.sh           # Docker build script
│
├── 📁 docs/                       # Documentation
│   ├── CLEANUP_NOTES.md          # Cleanup documentation
│   ├── LOCAL_SETUP.md            # Local setup guide
│   ├── deploy_steps.md           # Deployment steps
│   ├── TROUBLESHOOTING.md        # Troubleshooting guide
│   ├── DOCKER_GUIDE.txt          # Docker setup guide
│   └── docker-image-sharing.md  # Docker image sharing
│
├── 📁 data/                       # Data storage
│   └── (database files)
│
├── 📁 .github/                    # GitHub configuration
│   └── git-templates/
│
├── 🐳 Docker Files
│   ├── Dockerfile                # Main Dockerfile
│   ├── Dockerfile.backend        # Backend-specific Dockerfile
│   ├── Dockerfile.dev            # Development Dockerfile
│   ├── docker-compose.yml        # Main docker-compose
│   ├── docker-compose.dev.yml    # Development docker-compose
│   └── user-docker-compose.yml   # User-specific docker-compose
│
├── 📄 Configuration Files
│   ├── .env                      # Environment variables
│   ├── .gitignore               # Git ignore rules
│   ├── .dockerignore            # Docker ignore rules
│   ├── requirements.txt         # Python dependencies
│   ├── requirements_local.txt   # Local Python dependencies
│   └── .settings_key            # Settings key file
│
└── 📄 Root Files
    ├── README.md                 # Main project documentation
    ├── PROJECT_STRUCTURE.md     # This file
    └── user_tracking.db         # User tracking database
```

## 🎯 **Benefits of This Structure**

### ✅ **Clear Separation of Concerns**
- **Backend**: All Python/Flask code in one place
- **Frontend**: React application separate
- **Config**: All configuration files organized
- **Docs**: All documentation centralized

### ✅ **Easy Navigation**
- Developers know exactly where to find files
- Clear folder purposes
- Logical grouping of related files

### ✅ **Maintainability**
- Easy to add new features
- Clear boundaries between components
- Simplified deployment

### ✅ **Professional Structure**
- Industry-standard organization
- Scalable architecture
- Clean codebase

## 🚀 **Quick Start**

### **Backend Development**
```bash
cd backend/
python3 app.py
```

### **Frontend Development**
```bash
cd frontend/
npm start
```

### **Configuration**
```bash
cd config/
./set_jira_creds.sh
```

### **Documentation**
```bash
cd docs/
# View setup guides and troubleshooting
```
