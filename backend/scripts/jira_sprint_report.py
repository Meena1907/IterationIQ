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
    # Load from the project root .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', '.env')
    print(f"DEBUG - Loading .env from: {env_path}")
    load_dotenv(env_path)
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
    url = os.getenv('JIRA_URL')
    email = os.getenv('JIRA_EMAIL')
    api_token = os.getenv('JIRA_API_TOKEN')
    
    print(f"DEBUG - Environment variables:")
    print(f"  JIRA_URL: {url}")
    print(f"  JIRA_EMAIL: {email}")
    print(f"  JIRA_API_TOKEN: {'***' if api_token else 'None'}")
    
    return {
        'url': url,
        'email': email,
        'api_token': api_token
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
    jira_url, auth, headers = get_auth_and_headers()
except ValueError as e:
    print(f"Warning: {str(e)}")
    jira_url = auth = headers = None

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
        
        # Get ALL sprints from the board using pagination
        all_sprints = []
        start_at = 0
        max_results = 50
        
        print(f"\nFetching ALL sprints for board {board_id}")
        
        while True:
            url = f"{jira_url}/rest/agile/1.0/board/{board_id}/sprint"
            params = {
                    "startAt": start_at,
                    "maxResults": max_results
            }
            print(f"Fetching sprints {start_at} to {start_at + max_results}")
            resp = requests.get(url, headers=headers_obj, auth=auth_obj, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            sprints_batch = data.get("values", [])
            all_sprints.extend(sprints_batch)
            
            print(f"Fetched {len(sprints_batch)} sprints in this batch")
            
            # Check if we've got all sprints
            if data.get("isLast", True) or len(sprints_batch) == 0:
                break
            start_at += max_results
        
        if not all_sprints:
            print(f"No sprints found for board {board_id}")
            return []
        
        print(f"Total sprints found: {len(all_sprints)}")
        
        # Separate active and closed sprints
        active_sprints = [s for s in all_sprints if s.get("state") == "active"]
        closed_sprints = [s for s in all_sprints if s.get("state") == "closed" and s.get("endDate")]
        
        print(f"Active sprints: {len(active_sprints)}")
        print(f"Closed sprints: {len(closed_sprints)}")
        
        # Sort closed sprints by end date (newest first) to get the most recent ones
        closed_sprints.sort(key=lambda x: x.get("endDate", ""), reverse=True)
        
        # Return the last 15 recently closed sprints (most recent first)
        print(f"\nReturning last 15 recently closed sprints:")
        recent_sprints = closed_sprints[:15]
        for i, sprint in enumerate(recent_sprints, 1):
            print(f"{i}. {sprint.get('name')} (ended: {sprint.get('endDate')})")
        
        return recent_sprints
            
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
    """
    Analyze sprint using JIRA Sprint Report API (Greenhopper) with fallback to sprint issues API.
    Returns a dict with the metrics used by the frontend.
    """
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

        print(f"\nAnalyzing sprint: {sprint_name} (ID: {sprint_id})")

        # default values
        initial_planned = 0
        completed_count = 0
        not_completed_count = 0
        added_during_sprint = 0
        removed_during_sprint = 0
        initial_planned_sp = 0
        completed_sp = 0

        # Get JIRA credentials and URLs
        jira_url, auth_obj, headers_obj = get_auth_and_headers()

        # Call Greenhopper sprint report API (preferred - matches Jira UI)
        sprint_report_url = f"{jira_url}/rest/greenhopper/1.0/rapid/charts/sprintreport"
        params = {"rapidViewId": board_id, "sprintId": sprint_id}

        print(f"DEBUG - Fetching sprint report from: {sprint_report_url}")
        print(f"DEBUG - Params: rapidViewId={board_id}, sprintId={sprint_id}")

        sprint_report_resp = requests.get(sprint_report_url, headers=headers_obj, auth=auth_obj, params=params)
        print(f"DEBUG - Sprint report API response status: {sprint_report_resp.status_code}")

        if sprint_report_resp.status_code == 200:
            print("DEBUG - Using Greenhopper Sprint Report API (primary method)")
            sprint_report_data = sprint_report_resp.json()
            print(f"DEBUG - Sprint report API response keys: {list(sprint_report_data.keys())}")

            contents = sprint_report_data.get("contents", {})
            print(f"DEBUG - Contents keys: {list(contents.keys())}")

            # Issues arrays
            completed_issues_data = contents.get("completedIssues", []) or []
            incomplete_issues_data = contents.get("issuesNotCompletedInCurrentSprint", []) or []
            # Added issues during sprint
            added_keys = contents.get("issueKeysAddedDuringSprint", []) or []
            # Removed issues during sprint - check multiple possible field names
            removed_keys = (contents.get("issueKeysRemovedDuringSprint", []) or 
                          contents.get("puntedIssues", []) or [])
            
            print(f"DEBUG - Raw data from API:")
            print(f"  completedIssues count: {len(completed_issues_data)}")
            print(f"  issuesNotCompletedInCurrentSprint count: {len(incomplete_issues_data)}")
            print(f"  issueKeysRemovedDuringSprint: {removed_keys}")
            print(f"  issueKeysAddedDuringSprint: {added_keys}")

            # estimate sums
            all_issues_estimate_sum = contents.get("allIssuesEstimateSum", {}) or {}
            completed_issues_estimate_sum = contents.get("completedIssuesEstimateSum", {}) or {}
            issues_not_completed_initial_estimate_sum = contents.get("issuesNotCompletedInitialEstimateSum", {}) or {}

            # Compute numeric metrics
            completed_count = len(completed_issues_data)
            not_completed_count = len(incomplete_issues_data)
            
            # Handle added/removed keys - can be dict, list, or None
            if isinstance(added_keys, dict):
                added_during_sprint = len(added_keys)
            elif isinstance(added_keys, (list, tuple)):
                added_during_sprint = len(added_keys)
            else:
                added_during_sprint = 0
                
            if isinstance(removed_keys, dict):
                removed_during_sprint = len(removed_keys)
            elif isinstance(removed_keys, (list, tuple)):
                removed_during_sprint = len(removed_keys)
            else:
                removed_during_sprint = 0

    
            # --- Handle completed story points ---
            if completed_issues_estimate_sum.get("value") is not None:
                completed_sp = float(completed_issues_estimate_sum.get("value", 0) or 0)
            else:
                # Fallback: calculate from completed issues manually
                completed_sp = 0
                for issue in completed_issues_data:
                    story_points = (issue.get('fields', {}).get('customfield_10016') or 
                                    issue.get('fields', {}).get('customfield_10002') or 0)
                    if story_points:
                        completed_sp += float(story_points)
                print(f"DEBUG - Calculated completed_sp manually: {completed_sp}")

                # Ensure added_keys and removed_keys are sets for membership checks
                added_keys_set = set(added_keys.keys()) if isinstance(added_keys, dict) else set(added_keys)
                removed_keys_set = set(removed_keys) if isinstance(removed_keys, (list, tuple)) else set()


            # --- Calculate initial planned SP using existing fields ---
            initial_planned_sp = 0
            for issue in completed_issues_data + incomplete_issues_data:
                key = issue.get('key')
                story_points = (issue.get('fields', {}).get('customfield_10016') or 
                                issue.get('fields', {}).get('customfield_10002') or 0)
                if story_points:
                    # Include only issues that were planned at the START of the sprint
                    if (key not in added_keys_set) or (key in removed_keys_set):
                        initial_planned_sp += float(story_points)

            print(f"DEBUG - Calculated initial_planned_sp correctly: {initial_planned_sp}")
            
            # Calculate initial planned: issues that were planned at START of sprint
            # = (total issues at end) - (issues added during sprint) + (issues removed during sprint)
            initial_planned = (completed_count + not_completed_count) - added_during_sprint + removed_during_sprint

            print(f"DEBUG - Sprint Report API Results:")
            print(f"  allIssuesEstimateSum: {all_issues_estimate_sum}")
            print(f"  completedIssuesEstimateSum: {completed_issues_estimate_sum}")
            print(f"  issueKeysAddedDuringSprint: {added_keys}")
            print(f"  issueKeysRemovedDuringSprint: {removed_keys}")
            print(f"  added keys count: {added_during_sprint}")
            print(f"  removed keys count: {removed_during_sprint}")
            print(f"  initial_planned: {initial_planned}")
            print(f"  completed_count: {completed_count}")
            print(f"  not_completed_count: {not_completed_count}")

        else:
            # If sprint report fails, fallback to issues listing for the sprint
            print(f"DEBUG - Sprint report API failed with status {sprint_report_resp.status_code}")
            print(f"DEBUG - Response: {sprint_report_resp.text}")
            print("DEBUG - Using fallback method (basic sprint issues API)")

            issues_url = f"{jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=1000"
            issues_resp = requests.get(issues_url, headers=headers_obj, auth=auth_obj)

            if issues_resp.status_code == 200:
                issues_data = issues_resp.json()
                all_issues = issues_data.get("issues", []) or []
                print(f"DEBUG - Fallback API found {len(all_issues)} issues in sprint")

                completed_issues = []
                incomplete_issues = []

                for issue in all_issues:
                    status = issue.get('fields', {}).get('status', {}).get('name', '') or ''
                    status_norm = status.strip().lower()
                    # compare against DONE_STATUSES (normalize)
                    if status_norm in {s.lower() for s in DONE_STATUSES} or status_norm in ['done', 'closed', 'resolved']:
                        completed_issues.append(issue)
                    else:
                        incomplete_issues.append(issue)

                completed_count = len(completed_issues)
                not_completed_count = len(incomplete_issues)
                
                # Calculate story points
                completed_sp = 0
                initial_planned_sp = 0
                
                for issue in completed_issues:
                    story_points = issue.get('fields', {}).get('customfield_10016') or issue.get('fields', {}).get('customfield_10002') or 0
                    if story_points:
                        completed_sp += float(story_points)
                        
                for issue in all_issues:
                    story_points = issue.get('fields', {}).get('customfield_10016') or issue.get('fields', {}).get('customfield_10002') or 0
                    if story_points:
                        initial_planned_sp += float(story_points)
                
                # For fallback, we can't reliably determine added/removed during sprint
                # So we'll use the total count as initial planned
                initial_planned = len(all_issues)
                added_during_sprint = 0  # Can't determine from basic API
                removed_during_sprint = 0  # Can't determine from basic API
                
                print(f"DEBUG - Fallback calculations:")
                print(f"  Total issues in sprint: {len(all_issues)}")
                print(f"  Completed: {completed_count}, Not completed: {not_completed_count}")
                print(f"  Initial planned SP: {initial_planned_sp}, Completed SP: {completed_sp}")
            else:
                print(f"DEBUG - Fallback API also failed with status {issues_resp.status_code}")
                print(f"DEBUG - Response: {issues_resp.text}")
                # Keep defaults (zeros) and continue

        # Final derived calculations
        # completion percentage: prefer story points if available
        if initial_planned_sp > 0:
            completion_percentage_val = round((completed_sp / initial_planned_sp) * 100, 1)
        elif initial_planned > 0:
            completion_percentage_val = round((completed_count / initial_planned) * 100, 1)
        else:
            completion_percentage_val = None  # will be shown as "N/A"

        # scope change: added + removed (as count)
        scope_change = (added_during_sprint + removed_during_sprint)

        # Generate insights: provide completed_count, not_completed_count, scope_change and initial_planned
        insight = generate_insight(completed_count, not_completed_count, scope_change, initial_planned)

        # Format completion string
        completion_str = f"{completion_percentage_val}%" if completion_percentage_val is not None else "N/A"

        # Format date strings (strip time part)
        if start_date and start_date != "N/A":
            try:
                start_date = start_date.split('T')[0]
            except Exception:
                pass
        if end_date and end_date != "N/A":
            try:
                end_date = end_date.split('T')[0]
            except Exception:
                pass

        result = {
            "Sprint Name": sprint_name,
            "Start Date": start_date,
            "End Date": end_date,
            "Status": state,
            "Initial Planned": initial_planned,
            "Completed": completed_count,
            "Not Completed": not_completed_count,
            "Added During Sprint": added_during_sprint,
            "Removed During Sprint": removed_during_sprint,
            "Initial Planned SP": initial_planned_sp,
            "Completed SP": completed_sp,
            "Completion %": completion_str,
            "Insight": insight
        }

        print(f"DEBUG - Final result for {sprint_name}: {result}")
        return result

    except Exception as e:
        print(f"Error analyzing sprint: {str(e)}")
        import traceback
        print(traceback.format_exc())
        # Fallback return
        return {
            "Sprint Name": sprint.get("name", "Unknown Sprint"),
            "Start Date": sprint.get("startDate", "N/A").split('T')[0] if sprint.get("startDate") else "N/A",
            "End Date": sprint.get("endDate", "N/A").split('T')[0] if sprint.get("endDate") else "N/A",
            "Status": sprint.get("state", "N/A"),
            "Initial Planned": 0,
            "Completed": 0,
            "Not Completed": 0,
            "Added During Sprint": 0,
            "Removed During Sprint": 0,
            "Initial Planned SP": 0,
            "Completed SP": 0,
            "Completion %": "N/A",
            "Insight": "Analysis failed - using basic sprint data"
        }

def generate_jira_sprint_report(board_id):
    """
    Returns a list of dicts, one per sprint (last 15 sprints for each active sprint)
    """
    try:
        report = []
        sprints = get_sprints_for_board(board_id)
        print(f"DEBUG: get_sprints_for_board returned {len(sprints) if sprints else 0} sprints")
        
        if not sprints:
            print(f"No sprints found for board {board_id}")
            # Return dummy data for testing
            dummy_sprint = {
                "Sprint Name": "Test Sprint",
                "Start Date": "2024-01-01",
                "End Date": "2024-01-15",
                "Status": "closed",
                "Initial Planned": 10,
                "Completed": 8,
                "Not Completed": 2,
                "Added During Sprint": 0,
                "Removed During Sprint": 0,
                "Initial Planned SP": 0,
                "Completed SP": 0,
                "Completion %": "80.0%",
                "Insight": "Test data - no real sprints found"
            }
            return [dummy_sprint]
            
        # Use real analysis for each sprint
        for sprint in sprints:
            sprint_analysis = analyze_sprint(sprint, board_id)
            if sprint_analysis:
                report.append(sprint_analysis)
                
        print(f"DEBUG: Generated real analysis report with {len(report)} sprints")
        print(f"DEBUG: Report content: {report}")
        return report
    except Exception as e:
        print(f"Error generating sprint report: {str(e)}")
        return []

def generate_jira_sprint_report_progressive(board_id, task_id, sprint_report_tasks):
    """
    Returns a list of dicts, one per sprint, with progressive progress updates
    """
    try:
        print(f"DEBUG: Starting progressive sprint report for board {board_id}, task {task_id}")
        report = []
        sprints = get_sprints_for_board(board_id)
        print(f"DEBUG: get_sprints_for_board returned {len(sprints) if sprints else 0} sprints")
        
        if not sprints:
            print(f"No sprints found for board {board_id}")
            # Return dummy data for testing
            dummy_sprint = {
                "Sprint Name": "Test Sprint",
                "Start Date": "2024-01-01",
                "End Date": "2024-01-15",
                "Status": "closed",
                "Initial Planned": 10,
                "Completed": 8,
                "Not Completed": 2,
                "Added During Sprint": 0,
                "Removed During Sprint": 0,
                "Initial Planned SP": 0,
                "Completed SP": 0,
                "Completion %": "80.0%",
                "Insight": "Test data - no real sprints found"
            }
            sprint_report_tasks[task_id]['result'] = [dummy_sprint]
            sprint_report_tasks[task_id]['progress'] = 100
            sprint_report_tasks[task_id]['current_sprints'] = 1
            sprint_report_tasks[task_id]['total_sprints'] = 1
            return [dummy_sprint]
            
        total_sprints = len(sprints)
        print(f"DEBUG: Analyzing {total_sprints} sprints with progressive updates")
        
        # Use real analysis for each sprint with progress updates
        for i, sprint in enumerate(sprints):
            print(f"DEBUG: Analyzing sprint {i+1}/{total_sprints}: {sprint.get('name', 'Unknown')}")
            
            # Update progress: 30% base + (i/total_sprints) * 60% = 30% to 90%
            progress = 30 + int((i / total_sprints) * 60)
            sprint_report_tasks[task_id]['progress'] = progress
            sprint_report_tasks[task_id]['current_sprints'] = i
            sprint_report_tasks[task_id]['total_sprints'] = total_sprints
            
            try:
                sprint_analysis = analyze_sprint(sprint, board_id)
                if sprint_analysis:
                    report.append(sprint_analysis)
                    # Update partial results as we go
                    sprint_report_tasks[task_id]['partial_results'] = report.copy()
                    print(f"DEBUG: Updated partial results with {len(report)} sprints")
                else:
                    print(f"DEBUG: No analysis result for sprint {sprint.get('name', 'Unknown')}")
            except Exception as sprint_error:
                print(f"DEBUG: Error analyzing sprint {sprint.get('name', 'Unknown')}: {str(sprint_error)}")
                # Continue with next sprint
                continue
                
        # Final update
        sprint_report_tasks[task_id]['progress'] = 100
        sprint_report_tasks[task_id]['current_sprints'] = total_sprints
        sprint_report_tasks[task_id]['total_sprints'] = total_sprints
                
        print(f"DEBUG: Generated real analysis report with {len(report)} sprints")
        print(f"DEBUG: Report content: {report}")
        return report
    except Exception as e:
        print(f"Error generating sprint report: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        # Update task status to error
        if task_id in sprint_report_tasks:
            sprint_report_tasks[task_id]['status'] = 'error'
            sprint_report_tasks[task_id]['error'] = str(e)
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