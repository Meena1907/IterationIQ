import requests
from requests.auth import HTTPBasicAuth
from dateutil import parser
from datetime import datetime
import json
import time
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from settings_manager import settings_manager
except ImportError:
    # Fallback for direct execution - try to load from env
    from dotenv import load_dotenv
    load_dotenv()
    settings_manager = None

# --- CONFIGURATION ---
SPRINT_FIELD_ID = "customfield_10020"
DONE_STATUSES = {"CANCELLED", "DUPLICATE", "RESOLVED", "CLOSED"}

def get_jira_credentials():
    """Get JIRA credentials from settings or environment variables"""
    if settings_manager:
        credentials = settings_manager.get_jira_credentials()
        if credentials and all([credentials.get('url'), credentials.get('email'), credentials.get('api_token')]):
            return credentials
    
    # Fallback to environment variables
    return {
        'url': os.getenv('JIRA_URL'),
        'email': os.getenv('JIRA_EMAIL'),
        'api_token': os.getenv('JIRA_API_TOKEN')
    }

def get_auth_and_headers():
    """Get authentication and headers for JIRA API calls"""
    credentials = get_jira_credentials()
    
    if not credentials or not all([credentials.get('url'), credentials.get('email'), credentials.get('api_token')]):
        raise ValueError("JIRA credentials not configured. Please configure them in Settings.")
    
    auth = HTTPBasicAuth(credentials['email'], credentials['api_token'])
    headers = {"Accept": "application/json"}
    
    return credentials['url'], auth, headers

# Get initial credentials
try:
    JIRA_URL, auth, headers = get_auth_and_headers()
except ValueError as e:
    print(f"Warning: {str(e)}")
    JIRA_URL = auth = headers = None

def get_board_id(board_name):
    try:
        jira_url, auth_obj, headers_obj = get_auth_and_headers()
        url = f"{jira_url}/rest/agile/1.0/board"
        params = {"name": board_name}
        resp = requests.get(url, headers=headers_obj, auth=auth_obj, params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("values"):
            return data["values"][0]["id"]
        return None
    except ValueError as e:
        print(f"Error: {str(e)}")
        return None

def get_sprints_for_board(board_id):
    try:
        jira_url, auth_obj, headers_obj = get_auth_and_headers()
        url = f"{jira_url}/rest/agile/1.0/board/{board_id}/sprint"
        params = {
            "maxResults": 15  # Get more sprints to ensure we have enough
        }
        print(f"\nFetching sprints for board {board_id}")
        resp = requests.get(url, headers=headers_obj, auth=auth_obj, params=params)
        resp.raise_for_status()
        data = resp.json()
        all_sprints = data.get("values", [])
        
        if not all_sprints:
            print(f"No sprints found for board {board_id}")
            return []
        
        print(f"Total sprints found: {len(all_sprints)}")
        
        # Separate active and closed sprints
        active_sprints = [s for s in all_sprints if s.get("state") == "active"]
        closed_sprints = [s for s in all_sprints if s.get("state") == "closed" and s.get("endDate")]
        
        print(f"Active sprints: {len(active_sprints)}")
        print(f"Closed sprints: {len(closed_sprints)}")
        
        # Sort closed sprints by end date (newest first)
        closed_sprints.sort(key=lambda x: x.get("endDate", ""), reverse=True)
        
        # If there are active sprints, get last 15 closed sprints for each active sprint
        if active_sprints:
            result_sprints = []
            for active_sprint in active_sprints:
                active_name = active_sprint.get("name", "Unknown")
                active_start_date = active_sprint.get("startDate")
                print(f"\nProcessing active sprint: {active_name}")
                print(f"Start date: {active_start_date}")
                
                if active_start_date:
                    # Get sprints that ended before this active sprint started
                    relevant_closed = [s for s in closed_sprints if s.get("endDate") < active_start_date]
                    print(f"Found {len(relevant_closed)} closed sprints before this active sprint")
                    
                    # Take last 15 sprints for this active sprint
                    sprints_to_add = relevant_closed[:15]
                    print(f"Adding {len(sprints_to_add)} closed sprints to report")
                    for sprint in sprints_to_add:
                        print(f"- {sprint.get('name')} (ended: {sprint.get('endDate')})")
                    
                    result_sprints.extend(sprints_to_add)
            
            # Add active sprints
            print("\nAdding active sprints to report:")
            for sprint in active_sprints:
                print(f"- {sprint.get('name')} (started: {sprint.get('startDate')})")
            result_sprints.extend(active_sprints)
            
            # Sort by end date (active sprints will be at the end)
            result_sprints.sort(key=lambda x: x.get("endDate", "9999-12-31"), reverse=True)
            
            print(f"\nFinal report will contain {len(result_sprints)} sprints")
            return result_sprints
        else:
            # If no active sprints, just return last 15 closed sprints
            print("\nNo active sprints found, returning last 15 closed sprints")
            return closed_sprints[:15]
            
    except Exception as e:
        print(f"Error fetching sprints: {str(e)}")
        return []

def get_sprint_report(board_id, sprint_id):
    try:
        jira_url, auth_obj, headers_obj = get_auth_and_headers()
        url = f"{jira_url}/rest/greenhopper/1.0/rapid/charts/sprintreport"
        params = {
            "rapidViewId": board_id,
            "sprintId": sprint_id
        }
        resp = requests.get(url, headers=headers_obj, auth=auth_obj, params=params)
        resp.raise_for_status()
        return resp.json()
    except ValueError as e:
        print(f"Error: {str(e)}")
        return None

def generate_insight(completed, not_completed, scope_change, total_planned):
    completion_rate = (completed / total_planned * 100) if total_planned > 0 else 0
    scope_change_rate = (scope_change / total_planned * 100) if total_planned > 0 else 0
    
    insights = []
    
    if completion_rate >= 80:
        insights.append("✅ Good velocity")
    elif completion_rate < 50:
        insights.append("❌ Low delivery rate")
    else:
        insights.append("⚠️ Moderate delivery rate")
        
    if scope_change_rate >= 20:
        insights.append("⚠️ Unstable scope")
    elif scope_change_rate > 0:
        insights.append("ℹ️ Minor scope changes")
        
    return " | ".join(insights)

def analyze_sprint(sprint, board_id=None):
    try:
        if not sprint:
            print("Invalid sprint data")
            return None
            
        sprint_id = sprint.get("id")
        if not sprint_id:
            print("Missing sprint ID")
            return None
            
        sprint_name = sprint.get("name", "Unknown Sprint")
        start_date = sprint.get("startDate", "N/A")
        end_date = sprint.get("endDate", "N/A")
        state = sprint.get("state", "N/A")
        
        print(f"\nAnalyzing sprint: {sprint_name}")
        print(f"State: {state}")
        print(f"Start: {start_date}")
        print(f"End: {end_date}")
        
        # Get all issues in the sprint using the sprint report API (more accurate)
        try:
            jira_url, auth_obj, headers_obj = get_auth_and_headers()
            # Try to get sprint report first (more accurate for closed sprints)
            sprint_report_url = f"{jira_url}/rest/greenhopper/1.0/rapid/charts/sprintreport"
            params = {"rapidViewId": board_id or "2008", "sprintId": sprint_id}
            sprint_report_resp = requests.get(sprint_report_url, headers=headers_obj, auth=auth_obj, params=params)
            
            if sprint_report_resp.status_code == 200:
                sprint_report = sprint_report_resp.json()
                
                # Get the correct fields from Jira Sprint Report API
                completed_issues = sprint_report.get("contents", {}).get("completedIssues", [])
                incomplete_issues = sprint_report.get("contents", {}).get("incompletedIssues", [])
                punted_issues = sprint_report.get("contents", {}).get("puntedIssues", [])
                issues_not_completed_in_current_sprint = sprint_report.get("contents", {}).get("issuesNotCompletedInCurrentSprint", [])
                issue_keys_added_during_sprint = sprint_report.get("contents", {}).get("issueKeysAddedDuringSprint", [])
                
                # Debug: Print what we actually got from the API
                print(f"DEBUG - API Response fields:")
                print(f"  completedIssues: {len(completed_issues)} items")
                print(f"  incompletedIssues: {len(incomplete_issues)} items")
                print(f"  puntedIssues: {len(punted_issues)} items")
                print(f"  issuesNotCompletedInCurrentSprint: {len(issues_not_completed_in_current_sprint)} items")
                print(f"  issueKeysAddedDuringSprint: {len(issue_keys_added_during_sprint)} items")
                
                # Correct calculations
                completed_count = len(completed_issues)
                # For closed sprints, calculate not completed as: issues planned at start - completed - removed + added
                # This gives us the actual issues that were planned but not completed
                if len(incomplete_issues) == 0:
                    # If incompletedIssues is empty, calculate based on the formula
                    # Not completed = issuesNotCompletedInCurrentSprint - issueKeysAddedDuringSprint
                    # This gives us issues that were planned at start but not completed
                    not_completed_count = len(issues_not_completed_in_current_sprint) - len(issue_keys_added_during_sprint)
                    not_completed_count = max(0, not_completed_count)  # Ensure it's not negative
                    print(f"DEBUG - Calculated not_completed_count: {not_completed_count} (issuesNotCompletedInCurrentSprint: {len(issues_not_completed_in_current_sprint)} - issueKeysAddedDuringSprint: {len(issue_keys_added_during_sprint)})")
                else:
                    not_completed_count = len(incomplete_issues)
                    print(f"DEBUG - Using incompletedIssues for not_completed_count: {not_completed_count}")
                
                print(f"DEBUG - issuesNotCompletedInCurrentSprint count: {len(issues_not_completed_in_current_sprint)} (includes added issues)")
                
                added_during_sprint = len(issue_keys_added_during_sprint)
                removed_during_sprint = len(punted_issues)
                
                # Initial planned: issues present at sprint start
                # This should be: completed + not_completed + removed (issues that were planned at start)
                # We don't subtract added_during_sprint because those weren't part of initial plan
                initial_planned = completed_count + not_completed_count + removed_during_sprint
                
                # Calculate story points by making separate API calls to get full issue details
                initial_planned_sp = 0
                completed_sp = 0
                
                # Get story points for completed issues
                for issue in completed_issues:
                    try:
                        issue_key = issue.get('key')
                        if not issue_key:
                            continue
                            
                        # Make API call to get full issue details
                        issue_url = f"{jira_url}/rest/api/2/issue/{issue_key}"
                        issue_resp = requests.get(issue_url, headers=headers_obj, auth=auth_obj)
                        if issue_resp.status_code == 200:
                            issue_data = issue_resp.json()
                            fields = issue_data.get('fields', {})
                            
                            # Try multiple possible story points field names
                            story_points = 0
                            possible_fields = [
                                'customfield_10004',  # Common story points field
                                'customfield_10016',  # Standard story points field
                                'customfield_10008',  # Alternative story points field
                                'storyPoints',        # Direct story points field
                                'customfield_10026',  # Another common story points field
                                'customfield_10020',  # Yet another possibility
                                'customfield_10002',  # Additional common field
                                'customfield_10003',  # Additional common field
                                'customfield_10005',  # Additional common field
                                'customfield_10006',  # Additional common field
                                'customfield_10007',  # Additional common field
                                'customfield_10009',  # Additional common field
                                'customfield_10010',  # Additional common field
                                'customfield_10011',  # Additional common field
                                'customfield_10012',  # Additional common field
                                'customfield_10013',  # Additional common field
                                'customfield_10014',  # Additional common field
                                'customfield_10015',  # Additional common field
                                'customfield_10017',  # Additional common field
                                'customfield_10018',  # Additional common field
                                'customfield_10019',  # Additional common field
                                'customfield_10021',  # Additional common field
                                'customfield_10022',  # Additional common field
                                'customfield_10023',  # Additional common field
                                'customfield_10024',  # Additional common field
                                'customfield_10025',  # Additional common field
                                'customfield_10027',  # Additional common field
                                'customfield_10028',  # Additional common field
                                'customfield_10029',  # Additional common field
                                'customfield_10030',  # Additional common field
                            ]
                            
                            for field_name in possible_fields:
                                if field_name in fields and fields[field_name] is not None:
                                    story_points = fields[field_name]
                                    # Check if it's a numeric value (not a list or object)
                                    if isinstance(story_points, (int, float)) and story_points > 0:
                                        print(f"DEBUG: Found story points value: {story_points} for {issue_key} in field {field_name}")
                                        break
                                    else:
                                        print(f"DEBUG: Field {field_name} contains non-numeric value: {story_points} for {issue_key}")
                                        story_points = 0
                                else:
                                    story_points = 0
                            
                            completed_sp += story_points
                    except Exception as e:
                        print(f"DEBUG: Error processing story points for completed issue {issue.get('key', 'unknown')}: {str(e)}")
                        continue
                
                # Get story points for incomplete issues
                for issue in incomplete_issues:
                    try:
                        issue_key = issue.get('key')
                        if not issue_key:
                            continue
                            
                        # Make API call to get full issue details
                        issue_url = f"{jira_url}/rest/api/2/issue/{issue_key}"
                        issue_resp = requests.get(issue_url, headers=headers_obj, auth=auth_obj)
                        if issue_resp.status_code == 200:
                            issue_data = issue_resp.json()
                            fields = issue_data.get('fields', {})
                            
                            # Try multiple possible story points field names
                            story_points = 0
                            possible_fields = [
                                'customfield_10004',  # Common story points field
                                'customfield_10016',  # Standard story points field
                                'customfield_10008',  # Alternative story points field
                                'storyPoints',        # Direct story points field
                                'customfield_10026',  # Another common story points field
                                'customfield_10020',  # Yet another possibility
                                'customfield_10002',  # Additional common field
                                'customfield_10003',  # Additional common field
                                'customfield_10005',  # Additional common field
                                'customfield_10006',  # Additional common field
                                'customfield_10007',  # Additional common field
                                'customfield_10009',  # Additional common field
                                'customfield_10010',  # Additional common field
                                'customfield_10011',  # Additional common field
                                'customfield_10012',  # Additional common field
                                'customfield_10013',  # Additional common field
                                'customfield_10014',  # Additional common field
                                'customfield_10015',  # Additional common field
                                'customfield_10017',  # Additional common field
                                'customfield_10018',  # Additional common field
                                'customfield_10019',  # Additional common field
                                'customfield_10021',  # Additional common field
                                'customfield_10022',  # Additional common field
                                'customfield_10023',  # Additional common field
                                'customfield_10024',  # Additional common field
                                'customfield_10025',  # Additional common field
                                'customfield_10027',  # Additional common field
                                'customfield_10028',  # Additional common field
                                'customfield_10029',  # Additional common field
                                'customfield_10030',  # Additional common field
                            ]
                            
                            for field_name in possible_fields:
                                if field_name in fields and fields[field_name] is not None:
                                    story_points = fields[field_name]
                                    # Check if it's a numeric value (not a list or object)
                                    if isinstance(story_points, (int, float)) and story_points > 0:
                                        print(f"DEBUG: Found story points value: {story_points} for {issue_key} in field {field_name}")
                                        break
                                    else:
                                        print(f"DEBUG: Field {field_name} contains non-numeric value: {story_points} for {issue_key}")
                                        story_points = 0
                                else:
                                    story_points = 0
                            
                            initial_planned_sp += story_points
                    except Exception as e:
                        print(f"DEBUG: Error processing story points for incomplete issue {issue.get('key', 'unknown')}: {str(e)}")
                        continue
                
                # Add story points from completed issues to initial planned (they were planned at start)
                initial_planned_sp += completed_sp
                
                print(f"Using sprint report API:")
                print(f"Initial Planned: {initial_planned}")
                print(f"Completed: {completed_count}")
                print(f"Not Completed: {not_completed_count}")
                print(f"Added during sprint: {added_during_sprint}")
                print(f"Removed during sprint: {removed_during_sprint}")
                print(f"Initial Planned SP: {initial_planned_sp}")
                print(f"Completed SP: {completed_sp}")
                
                # Debug: Show available fields for first issue to help identify story points field
                if completed_issues:
                    first_issue = completed_issues[0]
                    fields = first_issue.get('fields', {})
                    print(f"DEBUG: Available fields in first completed issue:")
                    try:
                        for field_name, field_value in fields.items():
                            if 'story' in field_name.lower() or 'point' in field_name.lower() or 'customfield' in field_name.lower():
                                print(f"  {field_name}: {field_value}")
                    except Exception as e:
                        print(f"DEBUG: Error processing fields: {str(e)}")
                
            else:
                raise Exception("Sprint report API failed, falling back to issue API")
                
        except Exception as e:
            print(f"Sprint report API failed: {str(e)}, using fallback method")
            
            try:
                jira_url, auth_obj, headers_obj = get_auth_and_headers()
                # Fallback: Get all issues in the sprint
                issues_url = f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=100"
                issues_resp = requests.get(issues_url, headers=headers_obj, auth=auth_obj)
            except ValueError as cred_error:
                print(f"Credentials error in fallback: {str(cred_error)}")
                return None
            issues_resp.raise_for_status()
            issues_data = issues_resp.json()
            issues = issues_data.get("issues", [])
            
            print(f"Found {len(issues)} issues in sprint (fallback method)")
            
            completed_count = 0
            not_completed_count = 0
            added_during_sprint = 0
            removed_during_sprint = 0
            initial_planned_sp = 0
            completed_sp = 0
            initial_planned = 0  # Initialize initial_planned for fallback case
            
            sprint_start_dt = parser.parse(start_date) if start_date != "N/A" else None
            sprint_end_dt = parser.parse(end_date) if end_date != "N/A" else None
            
            for issue in issues:
                try:
                    issue_key = issue.get("key")
                    if not issue_key:
                        continue
                    
                    # For closed sprints, use current status as approximation
                    # (This is less accurate but better than nothing)
                    status = issue.get("fields", {}).get("status", {}).get("name", "").lower()
                    
                    # Try multiple possible story points field names
                    story_points = 0
                    fields = issue.get("fields", {})
                    
                    # Common story points field names
                    possible_fields = [
                        'customfield_10004',  # Common story points field
                        'customfield_10016',  # Standard story points field
                        'customfield_10008',  # Alternative story points field
                        'storyPoints',        # Direct story points field
                        'customfield_10026',  # Another common story points field
                        'customfield_10020',  # Yet another possibility
                        'customfield_10002',  # Additional common field
                        'customfield_10003',  # Additional common field
                        'customfield_10005',  # Additional common field
                        'customfield_10006',  # Additional common field
                        'customfield_10007',  # Additional common field
                        'customfield_10009',  # Additional common field
                        'customfield_10010',  # Additional common field
                        'customfield_10011',  # Additional common field
                        'customfield_10012',  # Additional common field
                        'customfield_10013',  # Additional common field
                        'customfield_10014',  # Additional common field
                        'customfield_10015',  # Additional common field
                        'customfield_10017',  # Additional common field
                        'customfield_10018',  # Additional common field
                        'customfield_10019',  # Additional common field
                        'customfield_10021',  # Additional common field
                        'customfield_10022',  # Additional common field
                        'customfield_10023',  # Additional common field
                        'customfield_10024',  # Additional common field
                        'customfield_10025',  # Additional common field
                        'customfield_10027',  # Additional common field
                        'customfield_10028',  # Additional common field
                        'customfield_10029',  # Additional common field
                        'customfield_10030',  # Additional common field
                    ]
                    
                    for field_name in possible_fields:
                        if field_name in fields and fields[field_name] is not None:
                            story_points = fields[field_name]
                            print(f"DEBUG: Found story points {story_points} for {issue_key} in field {field_name} (fallback)")
                            break
                    
                    if status in ["done", "closed", "resolved"]:
                        completed_count += 1
                        completed_sp += story_points
                    else:
                        not_completed_count += 1
                        initial_planned_sp += story_points
                        
                except Exception as e:
                    print(f"Error processing issue {issue.get('key', 'unknown')}: {str(e)}")
                    continue
            
            # Add completed story points to initial planned (they were planned at start)
            initial_planned_sp += completed_sp
            
            # Calculate initial planned count for fallback case
            initial_planned = completed_count + not_completed_count
        
        total_planned = completed_count + not_completed_count
        completion_pct = f"{(completed_count / total_planned * 100):.1f}%" if total_planned > 0 else "N/A"
        
        # Generate insights
        insight = generate_insight(
            completed_count,
            not_completed_count,
            added_during_sprint,
            total_planned
        )
        
        return {
            "Sprint Name": sprint_name,
            "Start Date": start_date[:10] if start_date != "N/A" else "N/A",
            "End Date": end_date[:10] if end_date != "N/A" else "N/A",
            "Status": state,
            "Initial Planned": initial_planned,
            "Completed": completed_count,
            "Not Completed": not_completed_count,
            "Added During Sprint": added_during_sprint,
            "Removed During Sprint": removed_during_sprint,
            "Initial Planned SP": initial_planned_sp,
            "Completed SP": completed_sp,
            "Completion %": completion_pct,
            "Insight": insight
        }
    except Exception as e:
        print(f"Error analyzing sprint: {str(e)}")
        return None

def generate_jira_sprint_report(board_id):
    """
    Returns a list of dicts, one per sprint (last 15 sprints for each active sprint)
    """
    try:
        report = []
        sprints = get_sprints_for_board(board_id)
        
        if not sprints:
            print(f"No sprints found for board {board_id}")
            return []
            
        for sprint in sprints:
            result = analyze_sprint(sprint, board_id)
            if result:
                report.append(result)
                
        print("DEBUG: About to return report to frontend:", report)
        return report
    except Exception as e:
        print(f"Error generating sprint report: {str(e)}")
        return []

# Only run main if executed directly
if __name__ == "__main__":
    BOARD_ID = "1697"  # Default for CLI usage
    report = generate_jira_sprint_report(BOARD_ID)
    print("\nSprint Report Summary (Last 15 Sprints for Each Active Sprint):")
    print(f"{'Sprint Name':<30} {'Start':<12} {'End':<12} {'Status':<10} {'Initial Planned':<20} {'Completed':<10} {'Not Completed':<15} {'Added':<10} {'Removed':<10} {'Completion %':<12} {'Insight':<40}")
    print("-" * 170)
    for result in report:
        print(f"{result['Sprint Name']:<30} {result['Start Date']:<12} {result['End Date']:<12} {result['Status']:<10} {result['Initial Planned']:<20} {result['Completed']:<10} {result['Not Completed']:<15} {result['Added During Sprint']:<10} {result['Removed During Sprint']:<10} {result['Completion %']:<12} {result['Insight']:<40}") 