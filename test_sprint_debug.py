#!/usr/bin/env python3

import sys
import os
sys.path.append('/home/hudson/jira_tpm/backend')

# Load environment variables first
from dotenv import load_dotenv
load_dotenv('/home/hudson/jira_tpm/.env')

from scripts.jira_sprint_report import get_sprints_for_board, analyze_sprint, get_auth_and_headers
import requests

def test_sprint_analysis():
    try:
        # Test with a specific board ID (you may need to adjust this)
        board_id = "1697"  # Replace with your actual board ID
        
        print("=== Testing Sprint Analysis ===")
        
        # Get sprints
        print(f"Fetching sprints for board {board_id}...")
        sprints = get_sprints_for_board(board_id)
        
        if not sprints:
            print("No sprints found!")
            return
            
        print(f"Found {len(sprints)} sprints")
        
        # Test the first sprint
        first_sprint = sprints[0]
        print(f"\nTesting sprint: {first_sprint.get('name')} (ID: {first_sprint.get('id')})")
        
        # Test direct API call
        jira_url, auth_obj, headers_obj = get_auth_and_headers()
        sprint_id = first_sprint.get('id')
        
        # Test sprint issues API directly
        issues_url = f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=1000"
        print(f"Testing direct API call: {issues_url}")
        
        response = requests.get(issues_url, headers=headers_obj, auth=auth_obj)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            issues = data.get('issues', [])
            print(f"Found {len(issues)} issues in sprint")
            
            if issues:
                print("Sample issue:")
                sample_issue = issues[0]
                print(f"  Key: {sample_issue.get('key')}")
                print(f"  Status: {sample_issue.get('fields', {}).get('status', {}).get('name')}")
                print(f"  Summary: {sample_issue.get('fields', {}).get('summary', 'N/A')[:50]}...")
            else:
                print("No issues found in sprint")
        else:
            print(f"API call failed: {response.text}")
            
        # Test full analysis
        print(f"\nTesting full sprint analysis...")
        result = analyze_sprint(first_sprint, board_id)
        if result:
            print("Analysis result:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("Analysis failed!")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_sprint_analysis()
