#!/usr/bin/env python3
"""
Minimal version of the Spark app for testing device tracking functionality
without requiring all dependencies.
"""

from flask import Flask, jsonify, request
import json
import os
import hashlib
from datetime import datetime

app = Flask(__name__)

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
        print(f"Error generating device fingerprint: {str(e)}")
        return None

def load_device_data():
    """Load device access data from file"""
    try:
        if os.path.exists(DEVICE_DATA_FILE):
            with open(DEVICE_DATA_FILE, 'r') as f:
                return json.load(f)
        return {'devices': {}, 'total_accesses': 0, 'last_updated': None}
    except Exception as e:
        print(f"Error loading device data: {str(e)}")
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
        print(f"Error saving device data: {str(e)}")

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
        print(f"Error tracking device access: {str(e)}")
        return 0

@app.route('/')
def index():
    """Simple homepage"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spark - Device Tracking Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .device-counter { 
                position: fixed; 
                bottom: 20px; 
                right: 20px; 
                background: #00ABE4; 
                color: white; 
                padding: 10px 15px; 
                border-radius: 20px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            }
            button { 
                background: #0066CC; 
                color: white; 
                border: none; 
                padding: 10px 20px; 
                border-radius: 5px; 
                cursor: pointer; 
                margin: 10px 5px;
            }
            button:hover { background: #0052A3; }
            .info { background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Spark - Device Tracking Test</h1>
            <div class="info">
                <h3>Device Tracking Feature Test</h3>
                <p>This is a minimal version to test the device tracking functionality.</p>
                <p>Click the buttons below to test the device tracking API endpoints.</p>
            </div>
            
            <button onclick="trackDevice()">Track Device Access</button>
            <button onclick="getDeviceCount()">Get Device Count</button>
            <button onclick="location.reload()">Refresh Page</button>
            
            <div id="result" style="margin-top: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; display: none;">
                <h4>API Response:</h4>
                <pre id="response"></pre>
            </div>
        </div>
        
        <div class="device-counter" id="deviceCounter">
            Loading device count...
        </div>
        
        <script>
            // Track device access when page loads
            trackDevice();
            
            async function trackDevice() {
                try {
                    const response = await fetch('/api/device/track', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const data = await response.json();
                    document.getElementById('response').textContent = JSON.stringify(data, null, 2);
                    document.getElementById('result').style.display = 'block';
                    updateDeviceCounter(data.device_count);
                } catch (error) {
                    document.getElementById('response').textContent = 'Error: ' + error.message;
                    document.getElementById('result').style.display = 'block';
                }
            }
            
            async function getDeviceCount() {
                try {
                    const response = await fetch('/api/device/count');
                    const data = await response.json();
                    document.getElementById('response').textContent = JSON.stringify(data, null, 2);
                    document.getElementById('result').style.display = 'block';
                    updateDeviceCounter(data.device_count);
                } catch (error) {
                    document.getElementById('response').textContent = 'Error: ' + error.message;
                    document.getElementById('result').style.display = 'block';
                }
            }
            
            function updateDeviceCounter(count) {
                const counter = document.getElementById('deviceCounter');
                counter.textContent = `📱 ${count} device${count !== 1 ? 's' : ''}`;
            }
        </script>
    </body>
    </html>
    """

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
        print(f"Error tracking device: {str(e)}")
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
        print(f"Error getting device count: {str(e)}")
        return jsonify({'error': 'Failed to get device count'}), 500

if __name__ == '__main__':
    print("🚀 Starting Spark Device Tracking Test Server...")
    print("📱 Device tracking functionality will be available at:")
    print("   - http://localhost:5000 (main page)")
    print("   - http://localhost:5000/api/device/track (POST - track access)")
    print("   - http://localhost:5000/api/device/count (GET - get count)")
    print("\n💡 Open multiple browser tabs/windows to test device tracking!")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)


