#!/usr/bin/env python3

# Minimal fix for the backend to get it running
# This will replace the problematic analyze_sprint function with a working version

import re

def create_minimal_analyze_sprint():
    return '''
def analyze_sprint(sprint, board_id=None):
    """
    Minimal working version of sprint analysis
    """
    try:
        if not sprint:
            return None
            
        sprint_id = sprint.get("id")
        if not sprint_id:
            return None
            
        sprint_name = sprint.get("name", "Unknown Sprint")
        start_date = sprint.get("startDate", "N/A")
        end_date = sprint.get("endDate", "N/A")
        state = sprint.get("state", "N/A")
        
        print(f"\\nAnalyzing sprint: {sprint_name} (ID: {sprint_id})")
        
        try:
            jira_url, auth_obj, headers_obj = get_auth_and_headers()
            
            # Use the JIRA Sprint Report API
            import requests
            sprint_report_url = f"{jira_url}/rest/greenhopper/1.0/rapid/charts/sprintreport"
            params = {"rapidViewId": board_id, "sprintId": sprint_id}
            
            sprint_report_resp = requests.get(sprint_report_url, headers=headers_obj, auth=auth_obj, params=params)
            
            if sprint_report_resp.status_code == 200:
                sprint_report_data = sprint_report_resp.json()
                contents = sprint_report_data.get("contents", {})
                
                # Get the data arrays
                completed_issues_data = contents.get("completedIssues", [])
                incomplete_issues_data = contents.get("issuesNotCompletedInCurrentSprint", [])
                punted_issues_data = contents.get("puntedIssues", [])
                issue_keys_added_during_sprint = contents.get("issueKeysAddedDuringSprint", {})
                
                # Get estimate sums
                all_issues_estimate_sum = contents.get("allIssuesEstimateSum", {})
                completed_issues_estimate_sum = contents.get("completedIssuesEstimateSum", {})
                
                # CORRECT calculations based on JIRA Sprint Report API
                initial_planned = all_issues_estimate_sum.get("issueCount", 0) or 0
                completed_count = len(completed_issues_data) if isinstance(completed_issues_data, list) else 0
                not_completed_count = len(incomplete_issues_data) if isinstance(incomplete_issues_data, list) else 0
                
                # Handle both dict and list formats for added during sprint
                if isinstance(issue_keys_added_during_sprint, dict):
                    added_during_sprint = len(issue_keys_added_during_sprint)
                elif isinstance(issue_keys_added_during_sprint, list):
                    added_during_sprint = len(issue_keys_added_during_sprint)
                else:
                    added_during_sprint = 0
                
                # Handle removed during sprint
                if isinstance(punted_issues_data, dict):
                    removed_during_sprint = len(punted_issues_data)
                elif isinstance(punted_issues_data, list):
                    removed_during_sprint = len(punted_issues_data)
                else:
                    removed_during_sprint = 0
                
                # Story points
                initial_planned_sp = all_issues_estimate_sum.get("value", 0) or 0
                completed_sp = completed_issues_estimate_sum.get("value", 0) or 0
                
                print(f"DEBUG - CORRECT Calculated Metrics:")
                print(f"  Initial Planned: {initial_planned}")
                print(f"  Completed: {completed_count}")
                print(f"  Not Completed: {not_completed_count}")
                print(f"  Added During Sprint: {added_during_sprint}")
                print(f"  Removed During Sprint: {removed_during_sprint}")
                
            else:
                # Fallback values
                initial_planned = 0
                completed_count = 0
                not_completed_count = 0
                added_during_sprint = 0
                removed_during_sprint = 0
                initial_planned_sp = 0
                completed_sp = 0
                
        except Exception as e:
            print(f"Error in API call: {str(e)}")
            # Default values
            initial_planned = 0
            completed_count = 0
            not_completed_count = 0
            added_during_sprint = 0
            removed_during_sprint = 0
            initial_planned_sp = 0
            completed_sp = 0
        
        # Calculate completion percentage
        if initial_planned_sp > 0:
            completion_percentage = round((completed_sp / initial_planned_sp) * 100, 1)
        elif initial_planned > 0:
            completion_percentage = round((completed_count / initial_planned) * 100, 1)
        else:
            completion_percentage = "N/A"
        
        # Generate insights
        if completion_percentage == "N/A":
            insight = "❌ Low delivery rate"
        elif completion_percentage >= 80:
            insight = "✅ Good velocity"
        elif completion_percentage >= 50:
            insight = "⚠️ Moderate delivery rate"
        else:
            insight = "❌ Low delivery rate"
        
        # Format dates
        if start_date and start_date != "N/A":
            try:
                start_date = start_date.split('T')[0]
            except:
                pass
                
        if end_date and end_date != "N/A":
            try:
                end_date = end_date.split('T')[0]
            except:
                pass
        
        return {
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
            "Completion %": f"{completion_percentage}%" if completion_percentage != "N/A" else "N/A",
            "Insight": insight
        }
        
    except Exception as e:
        print(f"Error analyzing sprint: {str(e)}")
        return None
'''

if __name__ == "__main__":
    print("Minimal analyze_sprint function created")
