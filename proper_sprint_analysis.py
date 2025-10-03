#!/usr/bin/env python3

"""
Proper Sprint Analysis using correct JIRA APIs
Based on the detailed explanation provided - this matches JIRA Sprint Report UI exactly
"""

def analyze_sprint_proper(sprint, board_id=None):
    """
    Analyze sprint using the CORRECT JIRA Sprint Report API fields
    This will match the JIRA Sprint Report UI exactly
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
        
        # Get JIRA credentials and URLs
        from scripts.jira_sprint_report import get_auth_and_headers
        jira_url, auth_obj, headers_obj = get_auth_and_headers()
        
        # Use the proper JIRA Sprint Report API (Greenhopper)
        import requests
        sprint_report_url = f"{jira_url}/rest/greenhopper/1.0/rapid/charts/sprintreport"
        params = {
            "rapidViewId": board_id,
            "sprintId": sprint_id
        }
        
        print(f"DEBUG - Fetching sprint report from: {sprint_report_url}")
        print(f"DEBUG - Params: rapidViewId={board_id}, sprintId={sprint_id}")
        
        sprint_report_resp = requests.get(sprint_report_url, headers=headers_obj, auth=auth_obj, params=params)
        
        print(f"DEBUG - Sprint report API response status: {sprint_report_resp.status_code}")
        
        if sprint_report_resp.status_code == 200:
            sprint_report_data = sprint_report_resp.json()
            contents = sprint_report_data.get("contents", {})
            
            print(f"DEBUG - Sprint report API response keys: {list(sprint_report_data.keys())}")
            print(f"DEBUG - Contents keys: {list(contents.keys())}")
            
            # Extract data using the CORRECT mapping from your explanation:
            
            # 1. Get the arrays
            completed_issues = contents.get("completedIssues", [])
            issues_not_completed = contents.get("issuesNotCompletedInCurrentSprint", [])
            punted_issues = contents.get("puntedIssues", [])
            issue_keys_added_during_sprint = contents.get("issueKeysAddedDuringSprint", [])
            issue_keys_removed_during_sprint = contents.get("issueKeysRemovedDuringSprint", [])
            
            # 2. Get the estimate sums
            completed_issues_estimate_sum = contents.get("completedIssuesEstimateSum", {})
            issues_not_completed_estimate_sum = contents.get("issuesNotCompletedEstimateSum", {})
            all_issues_estimate_sum = contents.get("allIssuesEstimateSum", {})
            
            # 3. Calculate metrics using CORRECT mapping:
            
            # Initial Planned (issues) = allIssuesEstimateSum.issueCount
            initial_planned_issues = all_issues_estimate_sum.get("issueCount", 0) or 0
            
            # Completed (issues) = completedIssues.length
            completed_count = len(completed_issues) if isinstance(completed_issues, list) else 0
            
            # Not Completed (issues) = issuesNotCompletedInCurrentSprint.length  
            not_completed_count = len(issues_not_completed) if isinstance(issues_not_completed, list) else 0
            
            # Added During Sprint = issueKeysAddedDuringSprint.length
            # Handle both list and dict formats from JIRA API
            if isinstance(issue_keys_added_during_sprint, dict):
                added_during_sprint = len(issue_keys_added_during_sprint)
            elif isinstance(issue_keys_added_during_sprint, list):
                added_during_sprint = len(issue_keys_added_during_sprint)
            else:
                added_during_sprint = 0
            
            # Removed During Sprint = issueKeysRemovedDuringSprint.length
            if isinstance(issue_keys_removed_during_sprint, dict):
                removed_during_sprint = len(issue_keys_removed_during_sprint)
            elif isinstance(issue_keys_removed_during_sprint, list):
                removed_during_sprint = len(issue_keys_removed_during_sprint)
            else:
                removed_during_sprint = 0
            
            # Initial Planned SP = allIssuesEstimateSum.value
            initial_planned_sp = all_issues_estimate_sum.get("value", 0) or 0
            
            # Completed SP = completedIssuesEstimateSum.value
            completed_sp = completed_issues_estimate_sum.get("value", 0) or 0
            
            # Completion % = (completedIssuesEstimateSum.value / allIssuesEstimateSum.value) × 100
            if initial_planned_sp > 0:
                completion_percentage = round((completed_sp / initial_planned_sp) * 100, 1)
            else:
                completion_percentage = "N/A"
            
            print(f"DEBUG - CORRECT Sprint Report API Results:")
            print(f"  All Issues Estimate Sum: {all_issues_estimate_sum}")
            print(f"  Completed Issues: {len(completed_issues)} items")
            print(f"  Issues Not Completed: {len(issues_not_completed)} items")
            print(f"  Issue Keys Added During Sprint: {len(issue_keys_added_during_sprint) if isinstance(issue_keys_added_during_sprint, (list, dict)) else 0} items")
            print(f"  Issue Keys Removed During Sprint: {len(issue_keys_removed_during_sprint) if isinstance(issue_keys_removed_during_sprint, (list, dict)) else 0} items")
            
            print(f"DEBUG - CORRECT Calculated Metrics:")
            print(f"  Initial Planned (issues): {initial_planned_issues}")
            print(f"  Completed (issues): {completed_count}")
            print(f"  Not Completed (issues): {not_completed_count}")
            print(f"  Added During Sprint: {added_during_sprint}")
            print(f"  Removed During Sprint: {removed_during_sprint}")
            print(f"  Initial Planned SP: {initial_planned_sp}")
            print(f"  Completed SP: {completed_sp}")
            print(f"  Completion %: {completion_percentage}")
            
        else:
            print(f"DEBUG - Sprint report API failed with status {sprint_report_resp.status_code}")
            print(f"DEBUG - Response: {sprint_report_resp.text}")
            return None
        
        # Generate insights based on completion percentage
        if completion_percentage == "N/A":
            insight = "❌ Low delivery rate"
        elif completion_percentage >= 80:
            insight = "✅ Good velocity"
        elif completion_percentage >= 50:
            insight = "⚠️ Moderate delivery rate"
        else:
            insight = "❌ Low delivery rate"
        
        # Add scope change insights
        scope_change_rate = (added_during_sprint + removed_during_sprint) / max(initial_planned_issues, 1) * 100
        if scope_change_rate > 20:
            insight += " | ⚠️ Unstable scope"
        elif scope_change_rate > 0:
            insight += " | ℹ️ Minor scope changes"
        
        # Format dates
        if start_date and start_date != "N/A":
            try:
                start_date = start_date.split('T')[0]  # Remove time part
            except:
                pass
                
        if end_date and end_date != "N/A":
            try:
                end_date = end_date.split('T')[0]  # Remove time part
            except:
                pass
        
        # Return the sprint analysis result using CORRECT mapping
        result = {
            "Sprint Name": sprint_name,
            "Start Date": start_date,
            "End Date": end_date,
            "Status": state,
            "Initial Planned": initial_planned_issues,  # This is the KEY fix - use allIssuesEstimateSum.issueCount
            "Completed": completed_count,
            "Not Completed": not_completed_count,
            "Added During Sprint": added_during_sprint,  # This is the KEY fix - handle dict format
            "Removed During Sprint": removed_during_sprint,
            "Initial Planned SP": initial_planned_sp,
            "Completed SP": completed_sp,
            "Completion %": f"{completion_percentage}%" if completion_percentage != "N/A" else "N/A",
            "Insight": insight
        }
        
        print(f"DEBUG - CORRECT Final result for {sprint_name}: {result}")
        return result
        
    except Exception as e:
        print(f"Error in sprint analysis: {str(e)}")
        return None

if __name__ == "__main__":
    print("✅ Proper Sprint Analysis implementation ready")
    print("Key fixes:")
    print("1. Initial Planned = allIssuesEstimateSum.issueCount (not calculated)")
    print("2. Added During Sprint = len(issueKeysAddedDuringSprint) - handles dict format")
    print("3. Uses proper JIRA Sprint Report API fields that match UI exactly")
