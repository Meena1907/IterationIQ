#!/usr/bin/env python3

# Test script to verify sprint calculation logic
# Based on the JIRA burndown chart data:
# - Initial Planned: 1 issue (at sprint start)
# - Scope changes: 3 issues added during sprint
# - Final state: 1 completed, 3 not completed

def test_sprint_calculation():
    # Simulate JIRA Sprint Report API response data
    # This is what we would get from /rest/greenhopper/1.0/rapid/charts/sprintreport
    
    # Mock data based on what JIRA burndown chart shows
    completed_issues_data = [
        {"key": "SCAL-267610", "status": "Done"}  # 1 completed issue
    ]
    
    incomplete_issues_data = [
        {"key": "SCAL-271515", "status": "In Progress"},  # 3 not completed issues
        {"key": "SCAL-272903", "status": "To Do"},
        {"key": "SCAL-273274", "status": "In Progress"}
    ]
    
    punted_issues_data = []  # No issues were removed
    
    issue_keys_added_during_sprint = [
        "SCAL-271515",  # Added Sep 10
        "SCAL-272903",  # Added Sep 16  
        "SCAL-273274"   # Added Sep 17
    ]  # 3 issues added during sprint
    
    # Calculate using our corrected logic
    completed_count = len(completed_issues_data)
    not_completed_count = len(incomplete_issues_data)
    added_during_sprint = len(issue_keys_added_during_sprint)
    removed_during_sprint = len(punted_issues_data)
    
    # Calculate initial planned correctly:
    # Initial planned = issues that were in the sprint at start (before scope changes)
    # This should be: completed + not_completed - added_during_sprint + removed_during_sprint
    initial_planned = completed_count + not_completed_count - added_during_sprint + removed_during_sprint
    
    print("=== Sprint Calculation Test ===")
    print(f"Completed issues: {completed_count}")
    print(f"Not completed issues: {not_completed_count}")
    print(f"Added during sprint: {added_during_sprint}")
    print(f"Removed during sprint: {removed_during_sprint}")
    print(f"Initial planned (calculated): {initial_planned}")
    print()
    print("Expected from JIRA burndown chart:")
    print(f"Initial planned: 1")
    print(f"Added during sprint: 3")
    print(f"Completed: 1")
    print(f"Not completed: 3")
    print()
    print("✅ MATCH!" if initial_planned == 1 and added_during_sprint == 3 and completed_count == 1 and not_completed_count == 3 else "❌ MISMATCH!")

if __name__ == "__main__":
    test_sprint_calculation()
