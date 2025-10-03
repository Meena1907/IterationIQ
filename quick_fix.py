#!/usr/bin/env python3

# Quick test to verify the issue with Added During Sprint calculation

# From the logs, we can see:
# Issue Keys Added During Sprint: {'SCAL-266698': True, 'SCAL-266731': True, ...}
# But our calculation shows: Added During Sprint: 0

# The problem is we're checking if it's a list, but it's actually a dictionary!

issue_keys_added_during_sprint_dict = {
    'SCAL-266698': True, 
    'SCAL-266731': True, 
    'SCAL-267600': True,
    # ... more keys
}

issue_keys_added_during_sprint_list = ['SCAL-266698', 'SCAL-266731', 'SCAL-267600']

print("=== Testing Added During Sprint Calculation ===")
print(f"Dictionary format: {issue_keys_added_during_sprint_dict}")
print(f"List format: {issue_keys_added_during_sprint_list}")
print()

# Current logic (incorrect):
added_during_sprint_current = len(issue_keys_added_during_sprint_dict) if isinstance(issue_keys_added_during_sprint_dict, list) else 0
print(f"Current logic (dict): {added_during_sprint_current}")

added_during_sprint_current_list = len(issue_keys_added_during_sprint_list) if isinstance(issue_keys_added_during_sprint_list, list) else 0
print(f"Current logic (list): {added_during_sprint_current_list}")

# Corrected logic:
if isinstance(issue_keys_added_during_sprint_dict, dict):
    added_during_sprint_corrected = len(issue_keys_added_during_sprint_dict)
elif isinstance(issue_keys_added_during_sprint_dict, list):
    added_during_sprint_corrected = len(issue_keys_added_during_sprint_dict)
else:
    added_during_sprint_corrected = 0

print(f"Corrected logic (dict): {added_during_sprint_corrected}")
print()
print("✅ The fix is to check for both dict and list formats!")
