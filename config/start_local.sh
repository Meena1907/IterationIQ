#!/bin/bash

# 🚀 Jira TPM Local Development Startup Script
# This script automates the local development setup

set -e  # Exit on any error

echo "🚀 Starting Jira TPM Local Development Setup..."

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ Error: Please run this script from the jira_tpm project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected files: app.py, requirements.txt"
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing Python dependencies..."
if [ -f "requirements_local.txt" ]; then
    echo "   Using requirements_local.txt (compatible versions)"
    pip install -r requirements_local.txt
else
    echo "   Using requirements.txt"
    pip install -r requirements.txt
fi

# Check if server is already running
echo "🔍 Checking if server is already running..."
if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "⚠️  Server is already running on port 8080"
    echo "   You can access it at: http://localhost:8080"
    echo "   To stop it, find the process and kill it:"
    echo "   lsof -i :8080"
    echo "   kill -9 <PID>"
    exit 0
fi

# Start the application
echo "🚀 Starting Jira TPM application..."
echo "   Backend: Flask server"
echo "   Frontend: React app (pre-built)"
echo "   Port: 8080"
echo ""
echo "📱 Access the application at: http://localhost:8080"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

# Start the Flask application
python3 app.py
