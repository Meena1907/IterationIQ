import requests
from requests.auth import HTTPBasicAuth
from dateutil import parser
from datetime import datetime
import json
import time

# --- CONFIGURATION ---
JIRA_URL = "https://thoughtspot.atlassian.net"  # <-- Replace with your Jira URL
EMAIL = "meena.singh@thoughtspot.com"                # <-- Replace with your Jira email
API_TOKEN = "ATATT3xFfGF0JszDBw4GIFkxCtqvSpztaOKsZQtNhSdMfUProZGCtlnx4iCidWqeUQTHBYdfpfyDdHMFaUbEeuCjvCjiLYfoL0IZOlf1F3E8Tqo-QNa7h7CS6M_syvuKXxmqmQfXCTs7hV7dR5L1iag-hqT0yI0XorBghQP9R_K8HveJshcvWag=23A6771A"                    # <-- Replace with your Jira API token
SPRINT_FIELD_ID = "customfield_10020"
DONE_STATUSES = {"CANCELLED", "DUPLICATE", "RESOLVED", "CLOSED"}

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

def get_board_id(board_name):
    url = f"{JIRA_URL}/rest/agile/1.0/board"
    params = {"name": board_name}
    resp = requests.get(url, headers=headers, auth=auth, params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("values"):
        return data["values"][0]["id"]
    return None

def get_sprints_for_board(board_id):
    try:
        url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint"
        params = {
            "maxResults": 5  # Get more sprints to ensure we have enough
        }
        print(f"\nFetching sprints for board {board_id}")
        resp = requests.get(url, headers=headers, auth=auth, params=params)
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
        
        # If there are active sprints, get last 5 closed sprints for each active sprint
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
                    
                    # Take last 5 sprints for this active sprint
                    sprints_to_add = relevant_closed[:5]
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
            # If no active sprints, just return last 5 closed sprints
            print("\nNo active sprints found, returning last 5 closed sprints")
            return closed_sprints[:5]
            
    except Exception as e:
        print(f"Error fetching sprints: {str(e)}")
        return []

def get_sprint_report(board_id, sprint_id):
    url = f"{JIRA_URL}/rest/greenhopper/1.0/rapid/charts/sprintreport"
    params = {
        "rapidViewId": board_id,
        "sprintId": sprint_id
    }
    resp = requests.get(url, headers=headers, auth=auth, params=params)
    resp.raise_for_status()
    return resp.json()

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
            # Try to get sprint report first (more accurate for closed sprints)
            sprint_report_url = f"{JIRA_URL}/rest/greenhopper/1.0/rapid/charts/sprintreport"
            params = {"rapidViewId": board_id or "2008", "sprintId": sprint_id}
            sprint_report_resp = requests.get(sprint_report_url, headers=headers, auth=auth, params=params)
            
            if sprint_report_resp.status_code == 200:
                sprint_report = sprint_report_resp.json()
                
                # Get completed and incomplete issues from sprint report
                completed_issues = sprint_report.get("contents", {}).get("completedIssues", [])
                incomplete_issues = sprint_report.get("contents", {}).get("incompletedIssues", [])
                
                # Get issues added/removed during sprint
                added_issues = sprint_report.get("contents", {}).get("issuesNotCompletedInCurrentSprint", [])
                removed_issues = sprint_report.get("contents", {}).get("puntedIssues", [])
                
                completed_count = len(completed_issues)
                
                # For "Not Completed", check the status of issues added during sprint
                not_completed_count = 0
                added_during_sprint = len(added_issues) if added_issues else 0
                
                # Check status of issues added during sprint
                if added_issues:
                    for issue in added_issues:
                        issue_key = issue.get("key")
                        if issue_key:
                            try:
                                # Get current status of the issue
                                issue_url = f"{JIRA_URL}/rest/api/2/issue/{issue_key}"
                                issue_resp = requests.get(issue_url, headers=headers, auth=auth)
                                if issue_resp.status_code == 200:
                                    issue_data = issue_resp.json()
                                    status = issue_data.get("fields", {}).get("status", {}).get("name", "").lower()
                                    if status not in ["done", "closed", "resolved"]:
                                        not_completed_count += 1
                            except Exception as e:
                                print(f"Error checking status for issue {issue_key}: {str(e)}")
                                # If we can't check status, assume not completed
                                not_completed_count += 1
                else:
                    # If no issues were added during sprint, use incomplete issues count
                    not_completed_count = len(incomplete_issues)
                
                removed_during_sprint = len(removed_issues) if removed_issues else 0
                
                print(f"Using sprint report API:")
                print(f"Completed: {completed_count}")
                print(f"Not Completed (from added during sprint): {not_completed_count}")
                print(f"Added during sprint: {added_during_sprint}")
                print(f"Removed during sprint: {removed_during_sprint}")
                
            else:
                raise Exception("Sprint report API failed, falling back to issue API")
                
        except Exception as e:
            print(f"Sprint report API failed: {str(e)}, using fallback method")
            
            # Fallback: Get all issues in the sprint
            issues_url = f"{JIRA_URL}/rest/agile/1.0/sprint/{sprint_id}/issue?maxResults=100"
            issues_resp = requests.get(issues_url, headers=headers, auth=auth)
            issues_resp.raise_for_status()
            issues_data = issues_resp.json()
            issues = issues_data.get("issues", [])
            
            print(f"Found {len(issues)} issues in sprint (fallback method)")
            
            completed_count = 0
            not_completed_count = 0
            added_during_sprint = 0
            removed_during_sprint = 0
            
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
                    if status in ["done", "closed", "resolved"]:
                        completed_count += 1
                    else:
                        not_completed_count += 1
                        
                except Exception as e:
                    print(f"Error processing issue {issue.get('key', 'unknown')}: {str(e)}")
                    continue
        
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
            "Completed": completed_count,
            "Not Completed": not_completed_count,
            "Added During Sprint": added_during_sprint,
            "Removed During Sprint": removed_during_sprint,
            "Completion %": completion_pct,
            "Insight": insight
        }
    except Exception as e:
        print(f"Error analyzing sprint: {str(e)}")
        return None

def generate_jira_sprint_report(board_id):
    """
    Returns a list of dicts, one per sprint (last 5 sprints for each active sprint)
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
    print("\nSprint Report Summary (Last 5 Sprints for Each Active Sprint):")
    print(f"{'Sprint Name':<30} {'Start':<12} {'End':<12} {'Status':<10} {'Completed':<10} {'Not Completed':<15} {'Added':<10} {'Removed':<10} {'Completion %':<12} {'Insight':<40}")
    print("-" * 170)
    for result in report:
        print(f"{result['Sprint Name']:<30} {result['Start Date']:<12} {result['End Date']:<12} {result['Status']:<10} {result['Completed']:<10} {result['Not Completed']:<15} {result['Added During Sprint']:<10} {result['Removed During Sprint']:<10} {result['Completion %']:<12} {result['Insight']:<40}") 