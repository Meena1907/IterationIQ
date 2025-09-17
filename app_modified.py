#!/usr/bin/env python3
"""
Modified version of the main Spark app that works without missing dependencies
Includes device tracking functionality
"""

from flask import Flask, jsonify, request, render_template, Response, send_from_directory
# Try to import flask_cors, but don't fail if it's missing
try:
    from flask_cors import CORS
    CORS_AVAILABLE = True
except ImportError:
    CORS_AVAILABLE = False
    print("Warning: flask_cors not available, CORS disabled")

import requests
import os
import base64
# Try to import dotenv, but don't fail if it's missing
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available, using environment variables only")

import logging
import sys
import traceback
from datetime import datetime, timedelta
import time
from dateutil import parser
import threading
import uuid
import csv
import io
import json
import hashlib

# Try to import openai, but don't fail if it's missing
try:
    from ai_sprint_insights import AISprintInsights
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("Warning: AI features not available")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enable CORS if available
if CORS_AVAILABLE:
    CORS(app)

# Device tracking functionality
DEVICE_DATA_FILE = 'data/device_access.json'

def get_device_fingerprint():
    """Generate a device fingerprint from request headers"""
    try:
        # Get various headers that can help identify a device
        user_agent = request.headers.get('User-Agent', '')
        accept_language = request.headers.get('Accept-Language', '')
        accept_encoding = request.headers.get('Accept-Encoding', '')
        connection = request.headers.get('Connection', '')
        
        # Create a fingerprint string
        fingerprint_data = f"{user_agent}|{accept_language}|{accept_encoding}|{connection}"
        
        # Generate a hash of the fingerprint
        device_id = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        return device_id
    except Exception as e:
        logger.error(f"Error generating device fingerprint: {str(e)}")
        return None

def load_device_data():
    """Load device access data from file"""
    try:
        if os.path.exists(DEVICE_DATA_FILE):
            with open(DEVICE_DATA_FILE, 'r') as f:
                return json.load(f)
        return {'devices': {}, 'total_accesses': 0, 'last_updated': None}
    except Exception as e:
        logger.error(f"Error loading device data: {str(e)}")
        return {'devices': {}, 'total_accesses': 0, 'last_updated': None}

def save_device_data(data):
    """Save device access data to file"""
    try:
        # Ensure data directory exists
        os.makedirs(os.path.dirname(DEVICE_DATA_FILE), exist_ok=True)
        
        data['last_updated'] = datetime.now().isoformat()
        with open(DEVICE_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving device data: {str(e)}")

def track_device_access():
    """Track device access and return current count"""
    try:
        device_id = get_device_fingerprint()
        if not device_id:
            return 0
            
        data = load_device_data()
        
        # Initialize device data if not exists
        if device_id not in data['devices']:
            data['devices'][device_id] = {
                'first_access': datetime.now().isoformat(),
                'last_access': datetime.now().isoformat(),
                'access_count': 0
            }
        
        # Update device access info
        data['devices'][device_id]['last_access'] = datetime.now().isoformat()
        data['devices'][device_id]['access_count'] += 1
        data['total_accesses'] += 1
        
        # Save updated data
        save_device_data(data)
        
        # Return unique device count
        return len(data['devices'])
        
    except Exception as e:
        logger.error(f"Error tracking device access: {str(e)}")
        return 0

def get_jira_credentials():
    """Get JIRA credentials from environment variables"""
    try:
        url = os.getenv('JIRA_URL', '').strip()
        email = os.getenv('JIRA_EMAIL', '').strip()
        api_token = os.getenv('JIRA_API_TOKEN', '').strip()
        
        if not all([url, email, api_token]):
            logger.warning("JIRA credentials not fully configured")
            return None
            
        return {
            'url': url,
            'email': email,
            'api_token': api_token
        }
    except Exception as e:
        logger.error(f"Error getting JIRA credentials: {str(e)}")
        return None

@app.route('/')
def index():
    """Serve the main application"""
    try:
        # Track device access
        device_count = track_device_access()
        
        # Serve the React app
        return send_from_directory('frontend/build', 'index.html')
    except Exception as e:
        logger.error(f"Error serving index: {str(e)}")
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spark - Sprint Analytics</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .status {{ background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .device-counter {{ 
                    position: fixed; 
                    bottom: 20px; 
                    right: 20px; 
                    background: #00ABE4; 
                    color: white; 
                    padding: 10px 15px; 
                    border-radius: 20px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                }}
                .feature {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 Spark - Sprint Analytics</h1>
                    <p>Team Performance Management Dashboard</p>
                </div>
                
                <div class="status">
                    <h3>✅ Application Status</h3>
                    <p>Spark is running successfully! Device tracking is active.</p>
                </div>
                
                <div class="feature">
                    <h3>📊 Sprint Analytics</h3>
                    <p>Comprehensive sprint reporting and trends analysis</p>
                </div>
                
                <div class="feature">
                    <h3>👤 Capacity Planning</h3>
                    <p>Individual performance analysis and optimization</p>
                </div>
                
                <div class="feature">
                    <h3>🏷️ Label Management</h3>
                    <p>Advanced label operations and search</p>
                </div>
                
                <div class="feature">
                    <h3>📱 Device Tracking</h3>
                    <p>Track unique device access (currently: {device_count} devices)</p>
                </div>
                
                <p><strong>Note:</strong> Some features may require additional dependencies. Check the logs for details.</p>
            </div>
            
            <div class="device-counter">
                📱 {device_count} device{device_count != 1 and 's' or ''}
            </div>
        </body>
        </html>
        """

@app.route('/<path:path>')
def serve_react(path):
    """Serve React app files"""
    try:
        return send_from_directory('frontend/build', path)
    except Exception as e:
        logger.error(f"Error serving file {path}: {str(e)}")
        return "File not found", 404

@app.route('/api/device/track', methods=['POST'])
def track_device():
    """Track device access and return device count"""
    try:
        device_count = track_device_access()
        return jsonify({
            'success': True,
            'device_count': device_count,
            'message': f'Access tracked. Total unique devices: {device_count}'
        })
    except Exception as e:
        logger.error(f"Error tracking device: {str(e)}")
        return jsonify({'error': 'Failed to track device access'}), 500

@app.route('/api/device/count', methods=['GET'])
def get_device_count():
    """Get current device count without tracking"""
    try:
        data = load_device_data()
        device_count = len(data['devices'])
        return jsonify({
            'success': True,
            'device_count': device_count,
            'total_accesses': data['total_accesses'],
            'last_updated': data['last_updated']
        })
    except Exception as e:
        logger.error(f"Error getting device count: {str(e)}")
        return jsonify({'error': 'Failed to get device count'}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get application status and available features"""
    try:
        data = load_device_data()
        device_count = len(data['devices'])
        
        return jsonify({
            'success': True,
            'app_name': 'Spark - Sprint Analytics',
            'version': '1.0.0',
            'status': 'running',
            'features': {
                'device_tracking': True,
                'cors': CORS_AVAILABLE,
                'dotenv': DOTENV_AVAILABLE,
                'ai_insights': AI_AVAILABLE,
                'jira_integration': get_jira_credentials() is not None
            },
            'device_count': device_count,
            'total_accesses': data['total_accesses']
        })
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

if __name__ == '__main__':
    print("🚀 Starting Spark - Sprint Analytics...")
    print("=" * 60)
    print("📱 Device tracking: ENABLED")
    print(f"🌐 CORS support: {'ENABLED' if CORS_AVAILABLE else 'DISABLED'}")
    print(f"🔧 Environment config: {'ENABLED' if DOTENV_AVAILABLE else 'DISABLED'}")
    print(f"🤖 AI insights: {'ENABLED' if AI_AVAILABLE else 'DISABLED'}")
    print(f"🔗 JIRA integration: {'ENABLED' if get_jira_credentials() else 'DISABLED'}")
    print("=" * 60)
    print("🌐 Application will be available at: http://localhost:5000")
    print("📊 Device tracking API: http://localhost:5000/api/device/count")
    print("🔍 Status API: http://localhost:5000/api/status")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


