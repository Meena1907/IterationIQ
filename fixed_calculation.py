# Corrected calculation logic for sprint metrics

def calculate_sprint_metrics(sprint_report_data):
    """
    Calculate sprint metrics from JIRA Sprint Report API data
    """
    # Get completed issues data
    completed_issues_data = sprint_report_data.get("contents", {}).get("completedIssues", [])
    incomplete_issues_data = sprint_report_data.get("contents", {}).get("issuesNotCompletedInCurrentSprint", [])
    punted_issues_data = sprint_report_data.get("contents", {}).get("puntedIssues", [])
    
    # Get the estimate sums (these are the key metrics we need)
    completed_issues_initial_estimate_sum = sprint_report_data.get("contents", {}).get("completedIssuesInitialEstimateSum", {})
    issues_not_completed_initial_estimate_sum = sprint_report_data.get("contents", {}).get("issuesNotCompletedInitialEstimateSum", {})
    completed_issues_estimate_sum = sprint_report_data.get("contents", {}).get("completedIssuesEstimateSum", {})
    
    # Get added/removed during sprint
    issue_keys_added_during_sprint = sprint_report_data.get("contents", {}).get("issueKeysAddedDuringSprint", {})
    
    # Extract issue counts (not story points) from the issue arrays
    completed_count = len(completed_issues_data) if isinstance(completed_issues_data, list) else 0
    not_completed_count = len(incomplete_issues_data) if isinstance(incomplete_issues_data, list) else 0
    
    # Added/Removed during sprint (count of issues)
    added_during_sprint = len(issue_keys_added_during_sprint) if isinstance(issue_keys_added_during_sprint, list) else 0
    removed_during_sprint = len(punted_issues_data) if isinstance(punted_issues_data, list) else 0
    
    # Calculate initial planned correctly:
    # Initial planned = issues that were in the sprint at start (before scope changes)
    # This should be: completed + not_completed - added_during_sprint + removed_during_sprint
    initial_planned = completed_count + not_completed_count - added_during_sprint + removed_during_sprint
    
    # Story Points (use the estimate sums for story points)
    initial_planned_sp = completed_issues_initial_estimate_sum.get("value", 0) or 0
    initial_planned_sp += issues_not_completed_initial_estimate_sum.get("value", 0) or 0
    completed_sp = completed_issues_estimate_sum.get("value", 0) or 0
    
    return {
        'completed_count': completed_count,
        'not_completed_count': not_completed_count,
        'initial_planned': initial_planned,
        'added_during_sprint': added_during_sprint,
        'removed_during_sprint': removed_during_sprint,
        'initial_planned_sp': initial_planned_sp,
        'completed_sp': completed_sp
    }
