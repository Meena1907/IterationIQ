from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
from scripts.jira_sprint_report import generate_jira_sprint_report, analyze_sprint
from scripts.user_capacity_analysis import analyze_user_capacity
import requests
import os
import base64
from dotenv import load_dotenv
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

# Configure logging to show all debug information
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Jira configuration
JIRA_URL = os.getenv('JIRA_URL')
JIRA_EMAIL = os.getenv('JIRA_EMAIL')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')

# Debug: Print environment variables status with masked values
logger.debug("Checking environment variables...")
logger.debug(f".env file exists: {os.path.exists('.env')}")
logger.debug(f".env file size: {os.path.getsize('.env') if os.path.exists('.env') else 0} bytes")
logger.debug(f"JIRA_URL: {JIRA_URL if JIRA_URL else 'Not set'}")
logger.debug(f"JIRA_EMAIL: {JIRA_EMAIL if JIRA_EMAIL else 'Not set'}")
logger.debug(f"JIRA_API_TOKEN length: {len(JIRA_API_TOKEN) if JIRA_API_TOKEN else 0}")

# Verify the values are loaded correctly
if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
    logger.error("Missing environment variables:")
    if not JIRA_URL:
        logger.error("- JIRA_URL is not set")
    if not JIRA_EMAIL:
        logger.error("- JIRA_EMAIL is not set")
    if not JIRA_API_TOKEN:
        logger.error("- JIRA_API_TOKEN is not set")
else:
    logger.info("All environment variables are set")
    logger.info(f"JIRA_URL: {JIRA_URL}")
    logger.info(f"JIRA_EMAIL: {JIRA_EMAIL}")
    logger.info(f"JIRA_API_TOKEN length: {len(JIRA_API_TOKEN)}")

app = Flask(__name__)
CORS(app)

# Global cache for labels
class LabelCache:
    def __init__(self):
        self.labels = set()
        self.last_updated = None
        self.cache_duration = timedelta(minutes=30)  # Cache for 30 minutes

    def needs_refresh(self):
        if not self.last_updated:
            return True
        return datetime.now() - self.last_updated > self.cache_duration

    def update(self, new_labels):
        self.labels = set(new_labels)
        self.last_updated = datetime.now()
        logger.info(f"Label cache updated with {len(self.labels)} labels")

    def get_labels(self):
        return sorted(list(self.labels))

    def search_labels(self, search_text):
        if not search_text:
            return []
        search_text = search_text.lower()
        return sorted([label for label in self.labels if search_text in label.lower()])

# Initialize the cache
label_cache = LabelCache()

# Rate limiting configuration
RATE_LIMIT_DELAY = 1  # Delay between requests in seconds
MAX_RETRIES = 3  # Maximum number of retries for rate-limited requests
RETRY_DELAY = 5  # Delay between retries in seconds

# In-memory storage for background sprint report tasks
sprint_report_tasks = {}

# In-memory storage for background sprint trends tasks
sprint_trends_tasks = {}

# In-memory storage for background capacity analysis tasks
capacity_analysis_tasks = {}

def make_jira_request(url, params=None, method='GET', json_data=None):
    """Make a request to Jira with rate limiting and retry logic"""
    retries = 0
    while retries < MAX_RETRIES:
        try:
            # Add delay between requests to respect rate limits
            time.sleep(RATE_LIMIT_DELAY)
            
            if method == 'GET':
                response = requests.get(url, headers=get_jira_headers(), params=params)
            else:
                response = requests.put(url, headers=get_jira_headers(), json=json_data)
            
            # Check for rate limiting
            if response.status_code == 429:
                retries += 1
                if retries < MAX_RETRIES:
                    logger.warning(f"Rate limited. Retrying in {RETRY_DELAY} seconds... (Attempt {retries}/{MAX_RETRIES})")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    logger.error("Max retries reached for rate-limited request")
                    return None
            
            return response
            
        except Exception as e:
            logger.error(f"Error making Jira request: {str(e)}")
            return None
    
    return None

@app.errorhandler(500)
def handle_500_error(e):
    logger.error(f"500 error occurred: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return jsonify({
        'error': 'Internal server error',
        'debug_info': {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
    }), 500

def get_jira_headers():
    try:
        # Verify environment variables are loaded
        if not JIRA_EMAIL or not JIRA_API_TOKEN:
            logger.error("Missing Jira credentials in environment variables")
            logger.error(f"JIRA_EMAIL: {'Set' if JIRA_EMAIL else 'Not set'}")
            logger.error(f"JIRA_API_TOKEN: {'Set' if JIRA_API_TOKEN else 'Not set'}")
            raise ValueError("Missing Jira credentials")

        # Debug: Print authentication details (without exposing the actual token)
        logger.debug("Generating Jira headers...")
        logger.debug(f"Using email: {JIRA_EMAIL}")
        logger.debug(f"API token length: {len(JIRA_API_TOKEN) if JIRA_API_TOKEN else 0}")
        
        # Create base64 encoded string of email:api_token
        auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
        auth_bytes = auth_string.encode('ascii')
        base64_bytes = base64.b64encode(auth_bytes)
        base64_string = base64_bytes.decode('ascii')
        
        headers = {
            'Authorization': f'Basic {base64_string}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Debug: Print the first few characters of the auth string (for debugging only)
        logger.debug(f"Auth string prefix: {auth_string[:10]}...")
        logger.debug(f"Base64 string prefix: {base64_string[:10]}...")
        
        return headers
    except Exception as e:
        logger.error(f"Error generating headers: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise

def test_jira_connection():
    """Test the Jira connection and return the response"""
    try:
        logger.debug("Testing Jira connection...")
        
        # Verify JIRA_URL is set
        if not JIRA_URL:
            logger.error("JIRA_URL is not set in environment variables")
            return None
            
        test_url = f'{JIRA_URL}/rest/api/2/myself'
        logger.debug(f"Testing connection to: {test_url}")
        
        try:
            headers = get_jira_headers()
            logger.debug("Headers generated successfully")
        except ValueError as e:
            logger.error(f"Failed to generate headers: {str(e)}")
            return None
        
        response = requests.get(
            test_url,
            headers=headers
        )
        
        logger.debug(f"Connection test response status: {response.status_code}")
        logger.debug(f"Connection test response headers: {response.headers}")
        
        if response.status_code != 200:
            logger.error(f"Connection test failed with status {response.status_code}")
            logger.error(f"Response text: {response.text}")
            if response.status_code == 401:
                logger.error("Authentication failed. Please check your email and API token.")
                logger.error("Make sure your .env file contains the correct JIRA_EMAIL and JIRA_API_TOKEN")
            elif response.status_code == 403:
                logger.error("Access forbidden. Please check your Jira permissions.")
        else:
            logger.info("Connection test successful!")
            logger.debug(f"Response data: {response.text}")
            
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Connection test error: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in connection test: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def get_project_info():
    try:
        logger.debug(f"Attempting to fetch projects from: {JIRA_URL}/rest/api/2/project")
        logger.debug(f"Using credentials - Email: {JIRA_EMAIL}")
        
        # Get all projects
        response = requests.get(
            f'{JIRA_URL}/rest/api/2/project',
            headers=get_jira_headers()
        )
        
        logger.debug(f"Project API Response Status: {response.status_code}")
        logger.debug(f"Project API Response Headers: {response.headers}")
        
        if response.status_code != 200:
            logger.error(f"Error response from Jira API: {response.text}")
            return None, []
            
        response.raise_for_status()
        projects = response.json()
        
        # Debug: Print all projects
        logger.info("Available projects:")
        for project in projects:
            logger.info(f"Key: {project['key']}, Name: {project['name']}")
        
        # Try to find SCAL project
        scal_project = None
        for project in projects:
            if project['key'].upper() == 'SCAL':
                scal_project = project
                break
        
        if not scal_project:
            # If not found by key, try by name
            for project in projects:
                if 'SCAL' in project['name'].upper():
                    scal_project = project
                    break
        
        if scal_project:
            logger.info(f"Found SCAL project: {scal_project['key']} ({scal_project['name']})")
        else:
            logger.warning("SCAL project not found")
            
        return scal_project, projects
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error getting project info: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
        return None, []
    except Exception as e:
        logger.error(f"Unexpected error getting project info: {str(e)}")
        return None, []

@app.route('/')
def index():
    return render_template('index.html')

def fetch_all_labels():
    """Fetch all labels from Jira and update the cache"""
    try:
        logger.debug("Starting fetch_all_labels...")
        
        # Search for issues with labels across all projects
        jql_query = 'labels is not EMPTY ORDER BY created DESC'
        search_url = f'{JIRA_URL}/rest/api/2/search'
        
        logger.debug(f"Using JQL query: {jql_query}")
        logger.debug(f"Search URL: {search_url}")
        
        all_labels = set()
        start_at = 0
        max_results = 1000  # Increased for faster initial load
        total_issues = None
        start_time = time.time()
        
        # First quick fetch to get initial results
        logger.debug("Performing initial quick fetch...")
        response = make_jira_request(
            search_url,
            params={
                'jql': jql_query,
                'startAt': 0,
                'maxResults': max_results,
                'fields': 'labels'
            }
        )
        
        if not response:
            logger.error("Failed to fetch initial labels")
            return False
            
        try:
            response_data = response.json()
            total_issues = response_data.get('total', 0)
            logger.info(f"Total issues to process: {total_issues}")
            
            # Process initial batch
            issues = response_data.get('issues', [])
            for issue in issues:
                fields = issue.get('fields', {})
                labels = fields.get('labels', [])
                if labels:
                    all_labels.update(labels)
            
            # Update cache with initial results
            initial_labels = sorted([str(label) for label in all_labels if label])
            label_cache.update(initial_labels)
            logger.info(f"Initial fetch: Found {len(initial_labels)} labels in {time.time() - start_time:.2f} seconds")
            
            # If we have more issues to process, continue in background
            if total_issues > max_results:
                logger.debug("Starting background fetch for remaining issues...")
                start_at = max_results
                
                while start_at < total_issues:
                    if time.time() - start_time > 10:  # Stop after 10 seconds
                        logger.info("Background fetch timeout reached")
                        break
                        
                    response = make_jira_request(
                        search_url,
                        params={
                            'jql': jql_query,
                            'startAt': start_at,
                            'maxResults': max_results,
                            'fields': 'labels'
                        }
                    )
                    
                    if not response:
                        logger.error("Failed to fetch remaining labels")
                        break
                        
                    response_data = response.json()
                    issues = response_data.get('issues', [])
                    
                    for issue in issues:
                        fields = issue.get('fields', {})
                        labels = fields.get('labels', [])
                        if labels:
                            all_labels.update(labels)
                    
                    start_at += len(issues)
                    
                    # Update cache with new labels
                    updated_labels = sorted([str(label) for label in all_labels if label])
                    label_cache.update(updated_labels)
                    logger.debug(f"Background fetch: Found {len(updated_labels)} labels so far")
                    
                    # Small delay to prevent rate limiting
                    time.sleep(0.5)
            
            logger.info(f"Final fetch: Found {len(all_labels)} unique labels in {time.time() - start_time:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Error processing response: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        logger.error(f"Error fetching labels: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

@app.route('/api/labels', methods=['GET'])
def get_labels():
    try:
        logger.debug("Starting get_labels endpoint")
        
        # Get search parameter
        search_text = request.args.get('search', '').strip()
        logger.debug(f"Search text: {search_text}")
        
        # Verify environment variables
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            logger.error("Missing Jira credentials")
            return jsonify({'error': 'Missing Jira credentials'}), 500
            
        # Check if we need to refresh the cache
        if label_cache.needs_refresh():
            logger.debug("Cache needs refresh, fetching new labels...")
            if not fetch_all_labels():
                logger.error("Failed to fetch labels")
                return jsonify({'error': 'Failed to fetch labels from Jira'}), 500
        
        # Get labels from cache
        all_labels = label_cache.get_labels()
        logger.debug(f"Retrieved {len(all_labels)} labels from cache")
        
        # If no search text, return all labels
        if not search_text:
            logger.debug("No search text, returning all labels")
            return jsonify({
                'labels': all_labels,
                'total_labels': len(all_labels),
                'cache_updated': label_cache.last_updated.isoformat() if label_cache.last_updated else None
            })

        # If search text is too short, return empty list
        if len(search_text) < 2:
            logger.debug("Search text too short, returning empty list")
            return jsonify({
                'labels': [],
                'total_labels': len(all_labels),
                'cache_updated': label_cache.last_updated.isoformat() if label_cache.last_updated else None
            })

        # Search in the cached labels
        search_text = search_text.lower()
        matching_labels = [label for label in all_labels if search_text in label.lower()]
        
        logger.info(f"Found {len(matching_labels)} labels matching '{search_text}'")
        
        return jsonify({
            'labels': matching_labels,
            'total_labels': len(all_labels),
            'cache_updated': label_cache.last_updated.isoformat() if label_cache.last_updated else None
        })
        
    except Exception as e:
        logger.error(f"Error in get_labels: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# Add a new endpoint to force refresh the cache
@app.route('/api/labels/refresh', methods=['POST'])
def refresh_labels():
    try:
        if fetch_all_labels():
            return jsonify({
                'message': 'Label cache refreshed successfully',
                'total_labels': len(label_cache.labels),
                'cache_updated': label_cache.last_updated.isoformat()
            })
        return jsonify({'error': 'Failed to refresh label cache'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/labels', methods=['POST'])
def add_label():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials. Please check your .env file.'}), 400

        data = request.json
        new_label = data.get('label')
        if not new_label:
            return jsonify({'error': 'Label is required'}), 400

        # Check if label already exists in cache
        existing_labels = label_cache.get_labels()
        if new_label in existing_labels:
            logger.info(f"Label '{new_label}' already exists")
            return jsonify({
                'message': 'Label already exists',
                'exists': True,
                'label': new_label
            }), 200

        # Get the SCAL project key
        projects_response = make_jira_request(f'{JIRA_URL}/rest/api/2/project')
        if not projects_response:
            return jsonify({'error': 'Failed to fetch projects'}), 500
            
        projects = projects_response.json()
        
        scal_project = None
        for project in projects:
            if project['name'].upper() == 'SCAL' or project['key'].upper() == 'SCAL':
                scal_project = project
                break
        
        if not scal_project:
            return jsonify({'error': 'SCAL project not found'}), 404

        # First, search for an existing issue in SCAL project to add the label to
        response = make_jira_request(
            f'{JIRA_URL}/rest/api/2/search',
            params={
                'jql': f'project = {scal_project["key"]}',
                'maxResults': 1
            }
        )
        
        if not response:
            return jsonify({'error': 'Failed to search for issues'}), 500
            
        issues = response.json().get('issues', [])
        if not issues:
            return jsonify({'error': f'No issues found in {scal_project["key"]} project to add label to'}), 404
            
        issue_key = issues[0]['key']
        current_labels = issues[0].get('fields', {}).get('labels', [])
        
        # Add the new label
        current_labels.append(new_label)
        
        # Update the issue with the new label
        update_response = make_jira_request(
            f'{JIRA_URL}/rest/api/2/issue/{issue_key}',
            method='PUT',
            json_data={'fields': {'labels': current_labels}}
        )
        
        if not update_response:
            return jsonify({'error': 'Failed to update issue'}), 500

        # Update the cache with the new label
        existing_labels.append(new_label)
        label_cache.update(existing_labels)
        
        return jsonify({
            'message': 'Label added successfully',
            'exists': False,
            'label': new_label
        })
    except Exception as e:
        logger.error(f"Error adding label: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/labels/<old_label>', methods=['PUT'])
def rename_label(old_label):
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials. Please check your .env file.'}), 400

        data = request.json
        new_label = data.get('new_label')
        if not new_label:
            return jsonify({'error': 'New label is required'}), 400

        # Get the SCAL project key
        projects_response = requests.get(
            f'{JIRA_URL}/rest/api/2/project',
            headers=get_jira_headers()
        )
        projects_response.raise_for_status()
        projects = projects_response.json()
        
        scal_project = None
        for project in projects:
            if project['name'].upper() == 'SCAL' or project['key'].upper() == 'SCAL':
                scal_project = project
                break
        
        if not scal_project:
            return jsonify({'error': 'SCAL project not found'}), 404

        # Search for issues with the old label in SCAL project
        response = requests.get(
            f'{JIRA_URL}/rest/api/2/search',
            headers=get_jira_headers(),
            params={
                'jql': f'project = {scal_project["key"]} AND labels = "{old_label}"',
                'maxResults': 1000,
                'fields': 'labels'
            }
        )
        response.raise_for_status()
        
        issues = response.json().get('issues', [])
        if not issues:
            return jsonify({'error': f'No issues found with label: {old_label}'}), 404
        
        # Update each issue with the new label
        for issue in issues:
            issue_key = issue['key']
            current_labels = issue.get('fields', {}).get('labels', [])
            if old_label in current_labels:
                current_labels.remove(old_label)
                current_labels.append(new_label)
                
                update_response = requests.put(
                    f'{JIRA_URL}/rest/api/2/issue/{issue_key}',
                    headers=get_jira_headers(),
                    json={'fields': {'labels': current_labels}}
                )
                update_response.raise_for_status()
        
        return jsonify({'message': 'Label renamed successfully'})
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            return jsonify({'error': f'Jira API error: {e.response.text}'}), e.response.status_code
        return jsonify({'error': 'Failed to connect to Jira'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/labels/<label>', methods=['DELETE'])
def delete_label(label):
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials. Please check your .env file.'}), 400

        # Get the SCAL project key
        projects_response = requests.get(
            f'{JIRA_URL}/rest/api/2/project',
            headers=get_jira_headers()
        )
        projects_response.raise_for_status()
        projects = projects_response.json()
        
        scal_project = None
        for project in projects:
            if project['name'].upper() == 'SCAL' or project['key'].upper() == 'SCAL':
                scal_project = project
                break
        
        if not scal_project:
            return jsonify({'error': 'SCAL project not found'}), 404

        # Search for issues with the label in SCAL project
        response = requests.get(
            f'{JIRA_URL}/rest/api/2/search',
            headers=get_jira_headers(),
            params={
                'jql': f'project = {scal_project["key"]} AND labels = "{label}"',
                'maxResults': 1000,
                'fields': 'labels'
            }
        )
        response.raise_for_status()
        
        issues = response.json().get('issues', [])
        if not issues:
            return jsonify({'error': f'No issues found with label: {label}'}), 404
        
        # Remove the label from each issue
        for issue in issues:
            issue_key = issue['key']
            current_labels = issue.get('fields', {}).get('labels', [])
            if label in current_labels:
                current_labels.remove(label)
                
                update_response = requests.put(
                    f'{JIRA_URL}/rest/api/2/issue/{issue_key}',
                    headers=get_jira_headers(),
                    json={'fields': {'labels': current_labels}}
                )
                update_response.raise_for_status()
        
        return jsonify({'message': 'Label deleted successfully'})
    except requests.exceptions.RequestException as e:
        if e.response is not None:
            return jsonify({'error': f'Jira API error: {e.response.text}'}), e.response.status_code
        return jsonify({'error': 'Failed to connect to Jira'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/tracks', methods=['GET'])
def get_jira_tracks():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials'}), 500
        response = make_jira_request(f'{JIRA_URL}/rest/api/2/project')
        if not response or response.status_code != 200:
            return jsonify({'error': 'Failed to fetch tracks from Jira'}), 500
        projects = response.json()
        tracks = [{'id': p['id'], 'key': p['key'], 'name': p['name']} for p in projects]
        return jsonify({'tracks': tracks})
    except Exception as e:
        logger.error(f"Error fetching tracks: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/tracks_customfield', methods=['GET'])
def get_jira_tracks_customfield():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials'}), 500
        # Try Jira Cloud v3 API for custom field context
        context_url = f"{JIRA_URL}/rest/api/3/field/customfield_15428/context"
        context_response = make_jira_request(context_url)
        logger.debug(f"Custom field context response status: {context_response.status_code if context_response else 'No response'}")
        logger.debug(f"Custom field context response text: {context_response.text if context_response else 'No response'}")
        if not context_response or context_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch custom field context', 'status': context_response.status_code if context_response else 'No response', 'text': context_response.text if context_response else 'No response'}), 500
        context_data = context_response.json()
        contexts = context_data.get('values', [])
        if not contexts:
            return jsonify({'error': 'No context found for custom field'}), 404
        context_id = contexts[0]['id']
        # Now get options for this context
        options_url = f"{JIRA_URL}/rest/api/3/field/customfield_15428/context/{context_id}/option"
        options_response = make_jira_request(options_url)
        logger.debug(f"Custom field options response status: {options_response.status_code if options_response else 'No response'}")
        logger.debug(f"Custom field options response text: {options_response.text if options_response else 'No response'}")
        if not options_response or options_response.status_code != 200:
            return jsonify({'error': 'Failed to fetch custom field options', 'status': options_response.status_code if options_response else 'No response', 'text': options_response.text if options_response else 'No response'}), 500
        options_data = options_response.json()
        options = options_data.get('values', [])
        tracks = [{'id': opt['id'], 'value': opt['value']} for opt in options]
        return jsonify({'tracks': tracks})
    except Exception as e:
        logger.error(f"Error fetching custom field options (v3): {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/boards_for_track', methods=['GET'])
def get_boards_for_track():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials'}), 500
        track = request.args.get('track', '').strip()
        logger.debug(f"Received track value for board search: '{track}'")
        if not track:
            return jsonify({'error': 'Missing track parameter'}), 400
        boards = []
        start_at = 0
        max_results = 50
        while True:
            boards_url = f"{JIRA_URL}/rest/agile/1.0/board?type=scrum&startAt={start_at}&maxResults={max_results}"
            response = make_jira_request(boards_url)
            if not response or response.status_code != 200:
                return jsonify({'error': 'Failed to fetch boards from Jira'}), 500
            data = response.json()
            for board in data.get('values', []):
                logger.debug(f"Found board: '{board['name']}' (id: {board['id']})")
                # Case-insensitive, trimmed prefix match
                if board['name'].strip().lower().startswith(track.lower()):
                    boards.append({'id': board['id'], 'name': board['name']})
            if data.get('isLast', True) or len(data.get('values', [])) == 0:
                break
            start_at += max_results
        logger.debug(f"Boards matching track '{track}': {boards}")
        return jsonify({'boards': boards})
    except Exception as e:
        logger.error(f"Error fetching boards for track: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/sprints_for_board', methods=['GET'])
def get_sprints_for_board():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials'}), 500
        board_id = request.args.get('board_id', '').strip()
        if not board_id:
            return jsonify({'error': 'Missing board_id parameter'}), 400

        # Step 1: Get ALL sprints from the board
        all_sprints = []
        start_at = 0
        max_results = 50
        
        while True:
            sprints_url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint?startAt={start_at}&maxResults={max_results}"
            response = make_jira_request(sprints_url)
            if not response or response.status_code != 200:
                return jsonify({'error': 'Failed to fetch sprints from Jira'}), 500
            data = response.json()
            
            all_sprints.extend(data.get('values', []))
                        
            if data.get('isLast', True) or len(data.get('values', [])) == 0:
                break
            start_at += max_results

        print(f"Total sprints fetched: {len(all_sprints)}")
        
        # Step 2: Filter for CLOSED sprints only and sort by endDate
        closed_sprints = []
        for sprint in all_sprints:
            if sprint.get('state') == 'closed' and sprint.get('endDate'):
                closed_sprints.append(sprint)
        
        print(f"Total closed sprints: {len(closed_sprints)}")
        
        # Sort by endDate (most recent first)
        closed_sprints.sort(key=lambda x: x.get('endDate', ''), reverse=True)
        
        # Step 3: Take the top 5 most recent closed sprints
        top_5_closed_sprints = closed_sprints[:5]
        
        print("Top 5 most recent CLOSED sprints:")
        for i, sprint in enumerate(top_5_closed_sprints):
            print(f"{i+1}. {sprint.get('name')} - End: {sprint.get('endDate')} - State: {sprint.get('state')}")
        
        # Step 4: Return the sprint info for the frontend
        result_sprints = []
        for sprint in top_5_closed_sprints:
            result_sprints.append({
                'id': sprint['id'],
                'name': sprint['name'],
                'state': sprint['state'],
                'startDate': sprint.get('startDate'),
                'endDate': sprint.get('endDate')
            })
        
        return jsonify({'sprints': result_sprints})
        
    except Exception as e:
        logger.error(f"Error fetching sprints for board: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/sprint_report', methods=['GET'])
def start_sprint_report_task():
    try:
        sprint_id = request.args.get('sprint_id', '').strip()
        board_id = request.args.get('board_id', '').strip()
        if not sprint_id or not board_id:
            return jsonify({'error': 'Missing sprint_id or board_id parameter'}), 400
        # Generate a unique task ID
        task_id = str(uuid.uuid4())
        # Start background thread
        thread = threading.Thread(target=process_sprint_report, args=(task_id, sprint_id, board_id))
        thread.start()
        # Return the task ID immediately
        return jsonify({'task_id': task_id})
    except Exception as e:
        logger.error(f"Error starting sprint report task: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/sprint_report_progress', methods=['GET'])
def get_sprint_report_progress():
    task_id = request.args.get('task_id', '').strip()
    if not task_id or task_id not in sprint_report_tasks:
        return jsonify({'error': 'Invalid or missing task_id'}), 400
    task = sprint_report_tasks[task_id]
    return jsonify({
        'progress': task.get('progress', 0),
        'status': task.get('status', 'pending'),
        'result': task.get('result') if task.get('status') == 'done' else None
    })

def process_sprint_report(task_id, sprint_id, board_id):
    try:
        sprint_report_tasks[task_id] = {'progress': 0, 'status': 'processing', 'result': None}
        # Fetch sprint details
        sprint_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}"
        sprint_resp = make_jira_request(sprint_url)
        if not sprint_resp or sprint_resp.status_code != 200:
            sprint_report_tasks[task_id]['status'] = 'error'
            sprint_report_tasks[task_id]['result'] = {'error': 'Failed to fetch sprint details'}
            return
        sprint = sprint_resp.json()
        # Fetch issues in the sprint
        issues_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=50"
        issues_resp = make_jira_request(issues_url)
        if not issues_resp or issues_resp.status_code != 200:
            sprint_report_tasks[task_id]['status'] = 'error'
            sprint_report_tasks[task_id]['result'] = {'error': 'Failed to fetch sprint issues'}
            return
        issues_data = issues_resp.json()
        issues = issues_data.get('issues', [])
        total_issues = len(issues)
        completed_count = 0
        not_completed_count = 0
        added_in_middle = 0
        removed_in_middle = 0
        added_in_middle_keys = []
        removed_in_middle_keys = []
        sprint_start = sprint.get('startDate')
        sprint_end = sprint.get('endDate')
        if sprint_start:
            sprint_start_dt = parser.parse(sprint_start)
            sprint_end_dt = parser.parse(sprint_end) if sprint_end else None
        else:
            sprint_start_dt = sprint_end_dt = None
        for idx, issue in enumerate(issues):
            status = issue['fields'].get('status', {}).get('name', '')
            if status.lower() in ['done', 'closed', 'resolved']:
                completed_count += 1
            else:
                not_completed_count += 1
            # Analyze changelog for added/removed in middle
            issue_key = issue['key']
            issue_url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}?expand=changelog"
            issue_resp = make_jira_request(issue_url)
            if not issue_resp or issue_resp.status_code != 200:
                continue
            changelog = issue_resp.json().get('changelog', {}).get('histories', [])
            added = False
            removed = False
            for history in changelog:
                created = history.get('created')
                created_dt = None
                if created:
                    try:
                        created_dt = parser.parse(created)
                    except Exception:
                        created_dt = None
                for item in history.get('items', []):
                    if item.get('field') == 'Sprint':
                        to_sprints = item.get('toString', '')
                        from_sprints = item.get('fromString', '')
                        if to_sprints and sprint.get('name') in to_sprints:
                            if sprint_start_dt and created_dt and created_dt > sprint_start_dt:
                                added = True
                        if from_sprints and sprint.get('name') in from_sprints:
                            if sprint_end_dt and created_dt and created_dt < sprint_end_dt:
                                removed = True
            if added:
                added_in_middle += 1
                added_in_middle_keys.append(issue_key)
            if removed:
                removed_in_middle += 1
                removed_in_middle_keys.append(issue_key)
            # Update progress
            sprint_report_tasks[task_id]['progress'] = int(((idx + 1) / total_issues) * 100)
        summary = {
            'sprint': {
                'id': sprint.get('id'),
                'name': sprint.get('name'),
                'state': sprint.get('state'),
                'startDate': sprint.get('startDate'),
                'endDate': sprint.get('endDate'),
                'goal': sprint.get('goal'),
            },
            'counts': {
                'completed': completed_count,
                'not_completed': not_completed_count,
                'added_in_middle': added_in_middle,
                'removed_in_middle': removed_in_middle
            },
            'added_in_middle_keys': added_in_middle_keys,
            'removed_in_middle_keys': removed_in_middle_keys
        }
        sprint_report_tasks[task_id]['status'] = 'done'
        sprint_report_tasks[task_id]['result'] = summary
    except Exception as e:
        sprint_report_tasks[task_id]['status'] = 'error'
        sprint_report_tasks[task_id]['result'] = {'error': str(e)}

@app.route('/api/jira/all_boards', methods=['GET'])
def get_all_boards():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials'}), 500
        
        # List of specific board IDs you want to fetch
        board_ids = ['1707']  # Add your specific board IDs here
        boards = []
        
        for board_id in board_ids:
            board_url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}"
            response = make_jira_request(board_url)
            if response and response.status_code == 200:
                board_data = response.json()
                boards.append({
                    'id': board_data['id'],
                    'name': board_data['name']
                })
            else:
                logger.warning(f"Failed to fetch board {board_id}: status={response.status_code if response else 'No response'}, text={response.text if response else 'No response'}")
        
        print("Successfully fetched boards:", [b['id'] for b in boards])
        print("Failed board IDs:", [bid for bid in board_ids if bid not in [b['id'] for b in boards]])
        
        return jsonify({'boards': boards})
    except Exception as e:
        logger.error(f"Error fetching all boards: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/sprint_trends', methods=['GET'])
def get_sprint_trends():
    try:
        if not all([JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN]):
            return jsonify({'error': 'Missing Jira credentials'}), 500

        board_id = request.args.get('board_id', '').strip()
        if not board_id:
            return jsonify({'error': 'Missing board_id parameter'}), 400

        # Get all sprints for the board (limit to 20 for speed)
        sprints = []
        start_at = 0
        max_results = 20
        while True:
            sprints_url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint?startAt={start_at}&maxResults={max_results}&state=active,closed"
            response = make_jira_request(sprints_url)
            if not response or response.status_code != 200:
                return jsonify({'error': 'Failed to fetch sprints from Jira'}), 500
            data = response.json()
            sprints.extend(data.get('values', []))
            if data.get('isLast', True) or len(data.get('values', [])) == 0 or len(sprints) >= 20:
                break
            start_at += max_results

        # Filter sprints with endDate and sort by endDate (most recent first)
        sprints = [s for s in sprints if s.get('endDate')]
        sprints.sort(key=lambda x: x.get('endDate', ''), reverse=True)

        # Take only the last 5 sprints (or fewer if not available)
        sprints = sprints[:5]

        logger.debug(f"Processing {len(sprints)} sprints for board {board_id}")

        sprint_details = []
        for sprint in sprints:
            sprint_id = sprint['id']
            sprint_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}"
            sprint_resp = make_jira_request(sprint_url)
            if not sprint_resp or sprint_resp.status_code != 200:
                logger.debug(f"Skipping sprint {sprint_id}: failed to fetch details")
                continue
            sprint_data = sprint_resp.json()
            sprint_end = sprint_data.get('endDate')
            if not sprint_end:
                logger.debug(f"Skipping sprint {sprint_id}: no endDate")
                continue
            from dateutil import parser
            sprint_end_dt = parser.parse(sprint_end)

            # Get all issues in the sprint
            issues_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=100"
            issues_resp = make_jira_request(issues_url)
            if not issues_resp or issues_resp.status_code != 200:
                logger.debug(f"Skipping sprint {sprint_id}: failed to fetch issues")
                continue
            issues_data = issues_resp.json()
            issues = issues_data.get('issues', [])
            logger.debug(f"Sprint {sprint_id} has {len(issues)} issues")

            completed_count = 0
            not_completed_count = 0

            for issue in issues:
                issue_key = issue['key']
                # Fetch changelog for the issue
                issue_url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}?expand=changelog"
                issue_resp = make_jira_request(issue_url)
                if not issue_resp or issue_resp.status_code != 200:
                    logger.debug(f"Skipping issue {issue_key}: failed to fetch changelog")
                    continue
                issue_data = issue_resp.json()
                changelog = issue_data.get('changelog', {}).get('histories', [])
                status_at_close = None
                last_status_time = None
                # Find the last status before sprint end
                for history in changelog:
                    created = history.get('created')
                    created_dt = None
                    if created:
                        try:
                            created_dt = parser.parse(created)
                        except Exception:
                            created_dt = None
                    for item in history.get('items', []):
                        if item.get('field') == 'status' and created_dt and created_dt <= sprint_end_dt:
                            status_at_close = item.get('toString')
                            last_status_time = created_dt
                # If no status change before sprint end, use current status
                if not status_at_close:
                    status_at_close = issue['fields'].get('status', {}).get('name', '')
                # Consider done/closed/resolved as completed
                if status_at_close.lower() in ['done', 'closed', 'resolved']:
                    completed_count += 1
                else:
                    not_completed_count += 1

            sprint_details.append({
                'id': sprint_id,
                'name': sprint_data.get('name'),
                'state': sprint_data.get('state'),
                'startDate': sprint_data.get('startDate'),
                'endDate': sprint_data.get('endDate'),
                'goal': sprint_data.get('goal'),
                'counts': {
                    'completed': completed_count,
                    'not_completed': not_completed_count
                }
            })
            logger.debug(f"Sprint {sprint_id} processed: completed={completed_count}, not_completed={not_completed_count}")

        return jsonify({'sprints': sprint_details})
    except Exception as e:
        logger.error(f"Error fetching sprint trends: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/sprint_trends_start', methods=['GET'])
def start_sprint_trends_task():
    try:
        board_id = request.args.get('board_id', '').strip()
        if not board_id:
            return jsonify({'error': 'Missing board_id parameter'}), 400
        task_id = str(uuid.uuid4())
        thread = threading.Thread(target=process_sprint_trends, args=(task_id, board_id))
        thread.start()
        return jsonify({'task_id': task_id})
    except Exception as e:
        logger.error(f"Error starting sprint trends task: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jira/sprint_trends_progress', methods=['GET'])
def get_sprint_trends_progress():
    task_id = request.args.get('task_id', '').strip()
    if not task_id or task_id not in sprint_trends_tasks:
        return jsonify({'error': 'Invalid or missing task_id'}), 400
    task = sprint_trends_tasks[task_id]
    # Always return current partial results, even if not done
    return jsonify({
        'progress': task.get('progress', 0),
        'status': task.get('status', 'pending'),
        'result': task.get('result')  # may be partial
    })

def process_sprint_trends(task_id, board_id):
    try:
        sprint_trends_tasks[task_id] = {'progress': 0, 'status': 'processing', 'result': {'sprints': []}}
        # Get all sprints for the board (limit to 20 for speed)
        sprints = []
        start_at = 0
        max_results = 20
        while True:
            sprints_url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint?startAt={start_at}&maxResults={max_results}&state=active,closed"
            response = make_jira_request(sprints_url)
            if not response or response.status_code != 200:
                sprint_trends_tasks[task_id]['status'] = 'error'
                sprint_trends_tasks[task_id]['result'] = {'error': 'Failed to fetch sprints from Jira'}
                return
            data = response.json()
            sprints.extend(data.get('values', []))
            if data.get('isLast', True) or len(data.get('values', [])) == 0 or len(sprints) >= 20:
                break
            start_at += max_results
        sprints = [s for s in sprints if s.get('endDate')]
        sprints.sort(key=lambda x: x.get('endDate', ''), reverse=True)
        sprints_to_add = sprints[:5]
        logger.debug(f"Processing {len(sprints_to_add)} sprints for board {board_id}")
        sprint_details = []
        total_issues = 0
        for sprint in sprints_to_add:
            sprint_id = sprint['id']
            sprint_name = sprint['name']
            sprint_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}"
            sprint_resp = make_jira_request(sprint_url)
            if not sprint_resp or sprint_resp.status_code != 200:
                logger.debug(f"Skipping sprint {sprint_id}: failed to fetch details")
                continue
            sprint_data = sprint_resp.json()
            sprint_end = sprint_data.get('endDate')
            if not sprint_end:
                logger.debug(f"Skipping sprint {sprint_id}: no endDate")
                continue
            from dateutil import parser
            sprint_end_dt = parser.parse(sprint_end)
            issues_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=100"
            issues_resp = make_jira_request(issues_url)
            if not issues_resp or issues_resp.status_code != 200:
                logger.debug(f"Skipping sprint {sprint_id}: failed to fetch issues")
                continue
            issues_data = issues_resp.json()
            issues = issues_data.get('issues', [])
            logger.debug(f"Sprint {sprint_id} has {len(issues)} issues")
            completed_count = 0
            not_completed_count = 0
            for issue in issues:
                issue_key = issue['key']
                issue_url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}?expand=changelog"
                issue_resp = make_jira_request(issue_url)
                if not issue_resp or issue_resp.status_code != 200:
                    logger.debug(f"Skipping issue {issue_key}: failed to fetch changelog")
                    continue
                issue_data = issue_resp.json()
                changelog = issue_data.get('changelog', {}).get('histories', [])
                # 1. Only count issues that were in the sprint at the end date
                was_in_sprint_at_end = False
                sprint_field_name = 'Sprint'
                last_sprint_change_before_end = None
                for history in changelog:
                    created = history.get('created')
                    created_dt = None
                    if created:
                        try:
                            created_dt = parser.parse(created)
                        except Exception:
                            created_dt = None
                    for item in history.get('items', []):
                        if item.get('field') == sprint_field_name and created_dt and created_dt <= sprint_end_dt:
                            # Check if sprint was added before or at end
                            to_sprints = item.get('to') or item.get('toString')
                            if to_sprints:
                                # to_sprints can be a string or list of sprint ids
                                if isinstance(to_sprints, list):
                                    if str(sprint_id) in [str(s) for s in to_sprints]:
                                        was_in_sprint_at_end = True
                                        last_sprint_change_before_end = created_dt
                                elif str(sprint_id) in str(to_sprints):
                                    was_in_sprint_at_end = True
                                    last_sprint_change_before_end = created_dt
                        if item.get('field') == sprint_field_name and created_dt and created_dt > sprint_end_dt:
                            # If sprint was removed after end, still count as in sprint at end
                            from_sprints = item.get('from') or item.get('fromString')
                            if from_sprints and str(sprint_id) in str(from_sprints):
                                was_in_sprint_at_end = True
                # If no changelog entry, check if current sprint field includes this sprint
                if not was_in_sprint_at_end:
                    sprint_field = issue['fields'].get('customfield_10020')  # This is usually the Sprint field
                    if sprint_field:
                        if isinstance(sprint_field, list):
                            if any(str(s.get('id')) == str(sprint_id) for s in sprint_field if isinstance(s, dict)):
                                was_in_sprint_at_end = True
                        elif isinstance(sprint_field, dict):
                            if str(sprint_field.get('id')) == str(sprint_id):
                                was_in_sprint_at_end = True
                if not was_in_sprint_at_end:
                    continue  # Skip this issue
                # 2. Use the status at the sprint end date
                status_at_close = None
                last_status_time = None
                for history in changelog:
                    created = history.get('created')
                    created_dt = None
                    if created:
                        try:
                            created_dt = parser.parse(created)
                        except Exception:
                            created_dt = None
                    for item in history.get('items', []):
                        if item.get('field') == 'status' and created_dt and created_dt <= sprint_end_dt:
                            status_at_close = item.get('toString')
                            last_status_time = created_dt
                if not status_at_close:
                    status_at_close = issue['fields'].get('status', {}).get('name', '')
                if status_at_close.lower() in ['done', 'closed', 'resolved']:
                    completed_count += 1
                else:
                    not_completed_count += 1
            sprint_details.append({
                'id': sprint_id,
                'name': sprint_data.get('name'),
                'state': sprint_data.get('state'),
                'startDate': sprint_data.get('startDate'),
                'endDate': sprint_data.get('endDate'),
                'goal': sprint_data.get('goal'),
                'counts': {
                    'completed': completed_count,
                    'not_completed': not_completed_count
                }
            })
            sprint_trends_tasks[task_id]['result'] = {'sprints': list(sprint_details)}
            logger.debug(f"Sprint {sprint_id} processed: completed={completed_count}, not_completed={not_completed_count}")
        sprint_trends_tasks[task_id]['status'] = 'done'
    except Exception as e:
        sprint_trends_tasks[task_id]['status'] = 'error'
        sprint_trends_tasks[task_id]['result'] = {'error': str(e)}

@app.route('/api/jira_sprint_report', methods=['GET'])
def api_jira_sprint_report():
    board_id = request.args.get('board_id', '').strip()
    fmt = request.args.get('format', 'json').lower()
    days_ago = request.args.get('days_ago', None)
    name_contains = request.args.get('name_contains', None)
    if not board_id:
        return jsonify({'error': 'Missing board_id parameter'}), 400
    try:
        # Step 1: Get the 5 most recent CLOSED sprints for this board
        print(f"Fetching most recent CLOSED sprints for board {board_id}")
        
        # Get ALL sprints from the board
        all_sprints = []
        start_at = 0
        max_results = 50
        
        while True:
            sprints_url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint?startAt={start_at}&maxResults={max_results}"
            response = make_jira_request(sprints_url)
            if not response or response.status_code != 200:
                return jsonify({'error': 'Failed to fetch sprints from Jira'}), 500
            data = response.json()
            
            all_sprints.extend(data.get('values', []))
                        
            if data.get('isLast', True) or len(data.get('values', [])) == 0:
                break
            start_at += max_results

        print(f"Total sprints fetched: {len(all_sprints)}")
        
        # Filter for CLOSED sprints only and sort by endDate
        closed_sprints = []
        for sprint in all_sprints:
            if sprint.get('state') == 'closed' and sprint.get('endDate'):
                closed_sprints.append(sprint)
        
        print(f"Total closed sprints: {len(closed_sprints)}")
        
        # Sort by endDate (most recent first)
        closed_sprints.sort(key=lambda x: x.get('endDate', ''), reverse=True)
        
        # Take the top 5 most recent closed sprints
        top_5_closed_sprints = closed_sprints[:5]
        
        print("Top 5 most recent CLOSED sprints for report:")
        for i, sprint in enumerate(top_5_closed_sprints):
            print(f"{i+1}. {sprint.get('name')} - End: {sprint.get('endDate')} - State: {sprint.get('state')}")
        
        # Step 2: Generate reports for these 5 closed sprints
        report = []
        for sprint in top_5_closed_sprints:
            print(f"Generating report for sprint: {sprint.get('name')}")
            result = analyze_sprint(sprint, board_id)
            if result:
                report.append(result)
        
        print(f"Generated reports for {len(report)} sprints")
        
        # Apply any additional filtering if requested
        filtered_report = report
        if days_ago is not None:
            try:
                days_ago = int(days_ago)
                cutoff_date = datetime.now() - timedelta(days=days_ago)
                filtered_report = [r for r in filtered_report if r.get('End Date') and datetime.strptime(r['End Date'].split('T')[0], '%Y-%m-%d') >= cutoff_date]
            except Exception:
                pass
        if name_contains:
            filtered_report = [r for r in filtered_report if name_contains.lower() in (r.get('Sprint Name', '').lower())]
        
        if fmt == 'csv':
            # Convert report to CSV
            output = io.StringIO()
            if filtered_report:
                writer = csv.DictWriter(output, fieldnames=filtered_report[0].keys())
                writer.writeheader()
                writer.writerows(filtered_report)
            else:
                output.write('No data')
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={
                    'Content-Disposition': f'attachment; filename=sprint_report_{board_id}.csv'
                }
            )
        else:
            return jsonify({'report': filtered_report})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/capacity/analyze', methods=['POST'])
def start_capacity_analysis():
    """Start a background capacity analysis task for a user"""
    try:
        data = request.get_json()
        user_email = data.get('user_email', '').strip()
        weeks_back = data.get('weeks_back', 8)
        
        if not user_email:
            return jsonify({'error': 'user_email is required'}), 400
        
        # Validate email format
        if '@' not in user_email:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Initialize task status
        capacity_analysis_tasks[task_id] = {
            'status': 'in_progress',
            'progress': 0,
            'result': None,
            'error': None,
            'user_email': user_email,
            'weeks_back': weeks_back,
            'started_at': datetime.now().isoformat()
        }
        
        # Start background task
        thread = threading.Thread(
            target=process_capacity_analysis,
            args=(task_id, user_email, weeks_back)
        )
        thread.start()
        
        return jsonify({
            'task_id': task_id,
            'status': 'started',
            'message': f'Capacity analysis started for {user_email}'
        })
        
    except Exception as e:
        logger.error(f"Error starting capacity analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/capacity/progress/<task_id>', methods=['GET'])
def get_capacity_analysis_progress(task_id):
    """Get the progress of a capacity analysis task"""
    if task_id not in capacity_analysis_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = capacity_analysis_tasks[task_id]
    return jsonify({
        'task_id': task_id,
        'status': task['status'],
        'progress': task['progress'],
        'user_email': task['user_email'],
        'weeks_back': task['weeks_back'],
        'started_at': task['started_at'],
        'result': task['result'],
        'error': task['error']
    })

def process_capacity_analysis(task_id, user_email, weeks_back):
    """Background task to process capacity analysis"""
    try:
        logger.info(f"Starting capacity analysis for {user_email} (last {weeks_back} weeks)")
        
        # Update progress
        capacity_analysis_tasks[task_id]['progress'] = 10
        capacity_analysis_tasks[task_id]['status'] = 'fetching_data'
        
        # Perform the analysis
        result = analyze_user_capacity(user_email, weeks_back)
        
        # Update progress
        capacity_analysis_tasks[task_id]['progress'] = 90
        
        if 'error' in result:
            capacity_analysis_tasks[task_id]['status'] = 'error'
            capacity_analysis_tasks[task_id]['error'] = result['error']
        else:
            capacity_analysis_tasks[task_id]['status'] = 'completed'
            capacity_analysis_tasks[task_id]['result'] = result
            capacity_analysis_tasks[task_id]['progress'] = 100
        
        logger.info(f"Capacity analysis completed for {user_email}")
        
    except Exception as e:
        logger.error(f"Error in capacity analysis for {user_email}: {str(e)}")
        capacity_analysis_tasks[task_id]['status'] = 'error'
        capacity_analysis_tasks[task_id]['error'] = str(e)

@app.route('/api/capacity/export/<task_id>', methods=['GET'])
def export_capacity_analysis(task_id):
    """Export capacity analysis results as CSV with user preferences"""
    if task_id not in capacity_analysis_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = capacity_analysis_tasks[task_id]
    if task['status'] != 'completed' or not task['result']:
        return jsonify({'error': 'Analysis not completed or no results available'}), 400
    
    try:
        result = task['result']
        
        # Get export settings from request args or use defaults
        delimiter = request.args.get('delimiter', ',')
        if delimiter == '\\t':
            delimiter = '\t'
        encoding = request.args.get('encoding', 'utf-8')
        include_headers = request.args.get('include_headers', 'true').lower() == 'true'
        
        # Create CSV content
        output = io.StringIO()
        
        # Write header information
        output.write(f"Capacity Analysis Report\n")
        output.write(f"User{delimiter}{result['user_email']}\n")
        output.write(f"Analysis Period{delimiter}{result['analysis_period']}\n")
        output.write(f"Overall Rating{delimiter}{result['overall_rating']}\n")
        output.write(f"Total Issues Analyzed{delimiter}{result['total_issues_analyzed']}\n")
        output.write(f"JIRA Link{delimiter}{result.get('jira_link', 'N/A')}\n")
        output.write(f"JQL Query{delimiter}{result.get('jql_query', 'N/A')}\n")
        output.write(f"Generated{delimiter}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write("\n")
        
        # Write issue breakdown
        output.write("Issue Breakdown\n")
        breakdown = result['issue_breakdown']
        
        output.write("Issue Types\n")
        if include_headers:
            output.write(f"Type{delimiter}Count{delimiter}Percentage\n")
        for issue_type, count in sorted(breakdown['by_type'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / breakdown['total_issues']) * 100
            output.write(f"{issue_type}{delimiter}{count}{delimiter}{percentage:.1f}%\n")
        output.write("\n")
        
        output.write("Priority Levels\n")
        if include_headers:
            output.write(f"Priority{delimiter}Count{delimiter}Percentage\n")
        for priority, count in sorted(breakdown['by_priority'].items(), key=lambda x: x[1], reverse=True):
            percentage = (count / breakdown['total_issues']) * 100
            output.write(f"{priority}{delimiter}{count}{delimiter}{percentage:.1f}%\n")
        output.write("\n")
        
        output.write("Completion Status\n")
        if include_headers:
            output.write(f"Status{delimiter}Count\n")
        completion = breakdown['by_completion']
        output.write(f"Completed{delimiter}{completion['completed']}\n")
        output.write(f"In Progress{delimiter}{completion['in_progress']}\n")
        output.write(f"Not Started{delimiter}{completion['not_started']}\n")
        output.write("\n")

        # Write key metrics
        output.write("Performance Metrics\n")
        if include_headers:
            output.write(f"Metric{delimiter}Value\n")
        metrics = result['metrics']
        output.write(f"Average Completed per Week{delimiter}{metrics['avg_completed_per_week']:.1f}\n")
        output.write(f"Average Started per Week{delimiter}{metrics['avg_started_per_week']:.1f}\n")
        output.write(f"Completion Rate{delimiter}{metrics['completion_rate']:.1%}\n")
        output.write(f"Average Hours per Week{delimiter}{metrics['avg_hours_per_week']:.1f}\n")
        output.write(f"Total Completed{delimiter}{metrics['total_completed']}\n")
        output.write(f"Total Started{delimiter}{metrics['total_started']}\n")
        output.write(f"Total Hours{delimiter}{metrics['total_hours']:.1f}\n")
        output.write("\n")
        
        # Write weekly summary
        output.write("Weekly Summary\n")
        if include_headers:
            output.write(f"Week{delimiter}Completed{delimiter}Started{delimiter}Hours Spent{delimiter}Issues Worked\n")
        for week in result['weekly_summary']:
            output.write(f"{week['week']}{delimiter}{week['completed']}{delimiter}{week['started']}{delimiter}{week['hours_spent']}{delimiter}{week['issues_worked']}\n")
        output.write("\n")
        
        # Write insights
        output.write("Insights\n")
        for insight in result['insights']:
            # Remove emojis for CSV
            clean_insight = ''.join(char for char in insight if ord(char) < 128)
            output.write(f"{clean_insight}\n")
        output.write("\n")
        
        # Write recommendations
        output.write("Recommendations\n")
        for rec in result['recommendations']:
            # Remove emojis for CSV
            clean_rec = ''.join(char for char in rec if ord(char) < 128)
            output.write(f"{clean_rec}\n")
        
        output.seek(0)
        
        # Generate filename
        user_name = result['user_email'].split('@')[0]
        filename = f"capacity_analysis_{user_name}_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting capacity analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Settings API endpoints
@app.route('/api/settings/test-jira', methods=['POST'])
def test_jira_connection_settings():
    """Test JIRA connection with provided credentials"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        email = data.get('email', '').strip()
        token = data.get('token', '').strip()
        
        if not all([url, email, token]):
            return jsonify({
                'success': False, 
                'error': 'Missing required fields'
            })
        
        # Remove trailing slash from URL
        if url.endswith('/'):
            url = url[:-1]
            
        # Test connection by getting current user info
        import requests
        from requests.auth import HTTPBasicAuth
        
        test_url = f"{url}/rest/api/2/myself"
        
        response = requests.get(
            test_url,
            auth=HTTPBasicAuth(email, token),
            timeout=10
        )
        
        if response.status_code == 200:
            user_info = response.json()
            return jsonify({
                'success': True,
                'user_info': {
                    'displayName': user_info.get('displayName', 'Unknown'),
                    'emailAddress': user_info.get('emailAddress', email)
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Authentication failed (HTTP {response.status_code})'
            })
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Connection timeout - please check your URL'
        })
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Connection error - please check your URL'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Connection test failed: {str(e)}'
        })

@app.route('/api/settings/save-jira', methods=['POST'])
def save_jira_config():
    """Save JIRA configuration securely"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        email = data.get('email', '').strip()
        token = data.get('token', '').strip()
        
        if not all([url, email, token]):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Remove trailing slash from URL
        if url.endswith('/'):
            url = url[:-1]
        
        # For this demo, we'll store in a simple way
        # In production, you'd want to encrypt the token and store securely
        settings_file = 'jira_settings.json'
        
        settings = {
            'url': url,
            'email': email,
            'token_encrypted': token  # In production, encrypt this
        }
        
        import json
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/settings/load-jira', methods=['GET'])
def load_jira_config():
    """Load saved JIRA configuration"""
    try:
        settings_file = 'jira_settings.json'
        
        if not os.path.exists(settings_file):
            return jsonify({
                'url': '',
                'email': '',
                'has_token': False
            })
        
        import json
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        return jsonify({
            'url': settings.get('url', ''),
            'email': settings.get('email', ''),
            'has_token': bool(settings.get('token_encrypted'))
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Share link storage (in production, use a database)
shared_reports = {}

@app.route('/api/capacity/share-link', methods=['POST'])
def create_share_link():
    """Create a shareable link for a capacity analysis report"""
    try:
        data = request.get_json()
        report_data = data.get('report_data')
        screenshot_url = data.get('screenshot_url')
        expires_in_days = data.get('expires_in_days', 7)
        
        if not report_data:
            return jsonify({'error': 'Report data is required'}), 400
        
        # Add screenshot URL to report data if provided
        if screenshot_url:
            report_data['screenshot_url'] = screenshot_url
        
        # Generate unique share ID
        share_id = str(uuid.uuid4())
        
        # Calculate expiration date
        expiration_date = datetime.now() + timedelta(days=expires_in_days)
        
        # Store the shared report
        shared_reports[share_id] = {
            'report_data': report_data,
            'created_at': datetime.now().isoformat(),
            'expires_at': expiration_date.isoformat(),
            'access_count': 0
        }
        
        # Generate share URL
        share_url = f"{request.host_url}share/{share_id}"
        
        return jsonify({
            'share_id': share_id,
            'share_url': share_url,
            'expires_at': expiration_date.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error creating share link: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/share/<share_id>')
def view_shared_report(share_id):
    """View a shared capacity analysis report"""
    try:
        if share_id not in shared_reports:
            return render_template('error.html', 
                                 error_title="Report Not Found",
                                 error_message="The shared report link is invalid or has expired."), 404
        
        shared_report = shared_reports[share_id]
        
        # Check if expired
        expiration_date = datetime.fromisoformat(shared_report['expires_at'])
        if datetime.now() > expiration_date:
            # Clean up expired report
            del shared_reports[share_id]
            return render_template('error.html',
                                 error_title="Report Expired",
                                 error_message="This shared report link has expired."), 410
        
        # Increment access count
        shared_report['access_count'] += 1
        
        # Render the shared report
        return render_template('shared_report.html', 
                             report_data=shared_report['report_data'],
                             share_info={
                                 'created_at': shared_report['created_at'],
                                 'expires_at': shared_report['expires_at'],
                                 'access_count': shared_report['access_count']
                             })
        
    except Exception as e:
        logger.error(f"Error viewing shared report: {str(e)}")
        return render_template('error.html',
                             error_title="Error",
                             error_message="An error occurred while loading the report."), 500

@app.route('/api/capacity/upload-screenshot', methods=['POST'])
def upload_screenshot():
    """Upload and temporarily store a screenshot for sharing"""
    try:
        if 'screenshot' not in request.files:
            return jsonify({'error': 'No screenshot file provided'}), 400
        
        file = request.files['screenshot']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate unique filename
        filename = f"screenshot_{str(uuid.uuid4())}.png"
        
        # In production, you'd want to use cloud storage (AWS S3, etc.)
        # For now, we'll store temporarily in memory or local storage
        file_path = f"temp_screenshots/{filename}"
        
        # Create directory if it doesn't exist
        import os
        os.makedirs('temp_screenshots', exist_ok=True)
        
        # Save the file
        file.save(file_path)
        
        # Generate public URL (in production, use cloud storage URL)
        screenshot_url = f"{request.host_url}temp_screenshots/{filename}"
        
        return jsonify({
            'screenshot_url': screenshot_url,
            'filename': filename,
            'message': 'Screenshot uploaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error uploading screenshot: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/temp_screenshots/<filename>')
def serve_screenshot(filename):
    """Serve uploaded screenshots"""
    try:
        from flask import send_from_directory
        return send_from_directory('temp_screenshots', filename)
    except Exception as e:
        logger.error(f"Error serving screenshot: {str(e)}")
        return "File not found", 404

if __name__ == '__main__':
    # Get port from environment variable or default to 8080
    port = int(os.getenv('PORT', 8080))
    # Get host from environment variable or default to localhost (0.0.0.0 for Docker)
    host = os.getenv('HOST', '0.0.0.0')
    # Get debug mode from environment variable
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug, host=host, port=port) 