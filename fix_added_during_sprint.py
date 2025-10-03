#!/usr/bin/env python3

# Quick fix for the "Added During Sprint" calculation issue
# This script will patch the jira_sprint_report.py file to handle dictionary format

import re

def fix_added_during_sprint_calculation():
    """
    Fix the calculation to handle both list and dictionary formats from JIRA API
    """
    file_path = '/home/hudson/jira_tpm/backend/scripts/jira_sprint_report.py'
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the problematic calculation
    # Current: len(issue_keys_added_during_sprint) if isinstance(issue_keys_added_during_sprint, list) else 0
    # Fixed: len(issue_keys_added_during_sprint) if isinstance(issue_keys_added_during_sprint, (list, dict)) else 0
    
    old_pattern = r'len\(issue_keys_added_during_sprint\)\s+if\s+isinstance\(issue_keys_added_during_sprint,\s+list\)\s+else\s+0'
    new_pattern = 'len(issue_keys_added_during_sprint) if isinstance(issue_keys_added_during_sprint, (list, dict)) else 0'
    
    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_pattern, content)
        print("✅ Fixed Added During Sprint calculation")
    else:
        print("⚠️ Pattern not found, checking alternative patterns...")
        
        # Alternative patterns to look for
        patterns = [
            (r'isinstance\(issue_keys_added_during_sprint,\s+list\)', 'isinstance(issue_keys_added_during_sprint, (list, dict))'),
            (r'if\s+isinstance\([^,]+,\s+list\)\s+else\s+0', lambda m: m.group(0).replace('list)', '(list, dict))')),
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                if callable(replacement):
                    content = re.sub(pattern, replacement, content)
                else:
                    content = re.sub(pattern, replacement, content)
                print(f"✅ Applied alternative fix for pattern: {pattern}")
                break
        else:
            print("❌ No matching patterns found")
    
    # Write back the file
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("File updated successfully")

if __name__ == "__main__":
    fix_added_during_sprint_calculation()
