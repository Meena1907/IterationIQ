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
BOARD_ID = "1697"                      # <-- Replace with your board ID
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

def get_latest_4_sprints(board_id):
    url = f"{JIRA_URL}/rest/agile/1.0/board/{board_id}/sprint"
    params = {
        "state": "closed",
        "maxResults": 50  # Get more sprints to ensure we have enough closed ones
    }
    resp = requests.get(url, headers=headers, auth=auth, params=params)
    resp.raise_for_status()
    sprints = resp.json().get("values", [])
    
    # Filter for closed sprints with end dates
    closed_sprints = [s for s in sprints if s.get("state") == "closed" and s.get("endDate")]
    
    # Sort by end date to ensure correct order (newest first)
    closed_sprints.sort(key=lambda x: x.get("endDate", ""), reverse=True)
    
    # Return the 4 most recent closed sprints
    return closed_sprints[:4]

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

def analyze_sprint(sprint, sprint_report):
    sprint_id = sprint["id"]
    sprint_name = sprint["name"]
    start_date = sprint.get("startDate", "N/A")
    end_date = sprint.get("endDate", "N/A")
    state = sprint.get("state", "N/A")
    
    # Extract data from sprint report
    contents = sprint_report.get("contents", {})
    completed_issues = contents.get("completedIssues", [])
    not_completed_issues = contents.get("issuesNotCompletedInCurrentSprint", [])
    added_issues = contents.get("issueKeysAddedDuringSprint", [])
    removed_issues = contents.get("puntedIssues", [])  # Issues removed during sprint
    
    # Match Jira UI: include all completed and not completed issues
    completed = completed_issues
    not_completed = not_completed_issues
    
    total_planned = len(completed) + len(not_completed)
    completion_pct = f"{(len(completed) / total_planned * 100):.1f}%" if total_planned > 0 else "N/A"
    
    # Generate insights
    insight = generate_insight(
        len(completed),
        len(not_completed),
        len(added_issues),
        total_planned
    )
    
    return {
        "Sprint Name": sprint_name,
        "Start Date": start_date[:10] if start_date != "N/A" else "N/A",
        "End Date": end_date[:10] if end_date != "N/A" else "N/A",
        "Status": state,
        "Completed": len(completed),
        "Not Completed": len(not_completed),
        "Added During Sprint": len(added_issues),
        "Removed During Sprint": len(removed_issues),
        "Completion %": completion_pct,
        "Insight": insight
    }

def main():
    print("\nSprint Report Summary (Last 4 Closed Sprints):")
    print(f"{'Sprint Name':<30} {'Start':<12} {'End':<12} {'Status':<10} {'Completed':<10} {'Not Completed':<15} {'Added':<10} {'Removed':<10} {'Completion %':<12} {'Insight':<40}")
    print("-" * 170)
    
    sprints = get_latest_4_sprints(BOARD_ID)
    for sprint in sprints:
        sprint_report = get_sprint_report(BOARD_ID, sprint["id"])
        result = analyze_sprint(sprint, sprint_report)
        print(f"{result['Sprint Name']:<30} {result['Start Date']:<12} {result['End Date']:<12} {result['Status']:<10} {result['Completed']:<10} {result['Not Completed']:<15} {result['Added During Sprint']:<10} {result['Removed During Sprint']:<10} {result['Completion %']:<12} {result['Insight']:<40}")

if __name__ == "__main__":
    main() 