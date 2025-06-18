import requests
from requests.auth import HTTPBasicAuth
from dateutil import parser
from datetime import datetime, timedelta
import json
from collections import defaultdict
import statistics

# --- CONFIGURATION ---
JIRA_URL = "https://thoughtspot.atlassian.net"  # <-- Replace with your Jira URL
EMAIL = "meena.singh@thoughtspot.com"                # <-- Replace with your Jira email
API_TOKEN = "ATATT3xFfGF0JszDBw4GIFkxCtqvSpztaOKsZQtNhSdMfUProZGCtlnx4iCidWqeUQTHBYdfpfyDdHMFaUbEeuCjvCjiLYfoL0IZOlf1F3E8Tqo-QNa7h7CS6M_syvuKXxmqmQfXCTs7hV7dR5L1iag-hqT0yI0XorBghQP9R_K8HveJshcvWag=23A6771A"                    # <-- Replace with your Jira API token

auth = HTTPBasicAuth(EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}

def get_user_issues(user_email, weeks_back=8):
    """
    Fetch ALL issues assigned to or worked on by a specific user in the last N weeks
    """
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(weeks=weeks_back)
        start_date_str = start_date.strftime('%Y-%m-%d')
        
        print(f"Fetching issues for {user_email} from {start_date_str} to present...")
        
        # JQL to find issues assigned to user (focus on assigned work only)
        jql = f'''
        assignee = "{user_email}" AND 
        updated >= "{start_date_str}"
        '''
        
        url = f"{JIRA_URL}/rest/api/2/search"
        params = {
            "jql": jql,
            "maxResults": 100,  # Keep batch size at 100 for API efficiency
            "expand": "changelog,worklog",
            "fields": "key,summary,status,assignee,created,updated,resolutiondate,worklog,priority,issuetype,timeestimate,timeoriginalestimate,timespent"
        }
        
        all_issues = []
        start_at = 0
        total_available = None
        
        while True:
            params["startAt"] = start_at
            response = requests.get(url, headers=headers, auth=auth, params=params)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get("issues", [])
            all_issues.extend(issues)
            
            # Get total count from first response
            if total_available is None:
                total_available = data.get("total", 0)
                print(f"Total issues available for user: {total_available}")
            
            print(f"Fetched batch: {len(issues)} issues (Total so far: {len(all_issues)}/{total_available})")
            
            # Check if we've reached the end using multiple conditions
            if (len(issues) == 0 or 
                data.get("isLast", False) or 
                len(all_issues) >= total_available or
                start_at + len(issues) >= total_available):
                break
                
            start_at += len(issues)
            
            # Safety check to prevent infinite loops
            if len(all_issues) > 10000:  # Reasonable upper limit
                print("Warning: Reached safety limit of 10,000 issues")
                break
        
        print(f"Found {len(all_issues)} total issues for analysis")
        return all_issues
        
    except Exception as e:
        print(f"Error fetching user issues: {str(e)}")
        return []

def analyze_weekly_performance(issues, user_email):
    """
    Analyze user's weekly performance patterns based on issues assigned to them
    """
    weekly_data = defaultdict(lambda: {
        'completed': 0,
        'started': 0,
        'time_spent': 0,
        'issues': []
    })
    
    # Track overall completion stats
    user_assigned_issues = []
    
    for issue in issues:
        issue_key = issue['key']
        fields = issue.get('fields', {})
        
        # Only analyze issues assigned to the user (since JQL already filters for this)
        assignee_email = fields.get('assignee', {}).get('emailAddress', '') if fields.get('assignee') else ''
        
        # Double-check that this issue is actually assigned to the user
        if assignee_email != user_email:
            continue
        
        # Track this issue for completion rate calculation
        current_status = fields.get('status', {}).get('name', '').lower()
        is_completed = current_status in ['done', 'closed', 'resolved']
        user_assigned_issues.append({
            'key': issue_key,
            'completed': is_completed,
            'status': current_status
        })
        
        # Get issue creation and resolution dates
        created_date = parser.parse(fields.get('created')) if fields.get('created') else None
        resolved_date = parser.parse(fields.get('resolutiondate')) if fields.get('resolutiondate') else None
        
        # Track completion by week
        if resolved_date and is_completed:
            week_key = resolved_date.strftime('%Y-W%U')
            weekly_data[week_key]['completed'] += 1
            weekly_data[week_key]['issues'].append({
                'key': issue_key,
                'action': 'completed',
                'date': resolved_date
            })
        
        # Analyze changelog for when user started work on assigned issues
        changelog = issue.get('changelog', {}).get('histories', [])
        for history in changelog:
            created_date = parser.parse(history['created'])
            week_key = created_date.strftime('%Y-W%U')
            
            for item in history.get('items', []):
                if item.get('field') == 'status':
                    from_status = item.get('fromString', '').lower()
                    to_status = item.get('toString', '').lower()
                    
                    # Track when issue was moved to in-progress (started)
                    if (from_status in ['to do', 'open', 'backlog', 'new'] and 
                        to_status in ['in progress', 'in development', 'in review'] and
                        assignee_email == user_email):
                        
                        weekly_data[week_key]['started'] += 1
                        weekly_data[week_key]['issues'].append({
                            'key': issue_key,
                            'action': 'started',
                            'date': created_date
                        })
        
        # Analyze worklog for time spent
        worklogs = fields.get('worklog', {}).get('worklogs', [])
        for worklog in worklogs:
            author_email = worklog.get('author', {}).get('emailAddress', '')
            if author_email == user_email:
                started_date = parser.parse(worklog['started'])
                week_key = started_date.strftime('%Y-W%U')
                time_spent_seconds = worklog.get('timeSpentSeconds', 0)
                weekly_data[week_key]['time_spent'] += time_spent_seconds / 3600  # Convert to hours
    
    # Store user assigned issues for completion rate calculation
    weekly_data['_user_assigned_issues'] = user_assigned_issues
    
    return dict(weekly_data)

def calculate_performance_metrics(weekly_data):
    """
    Calculate key performance metrics
    """
    if not weekly_data:
        return {}
    
    # Get user assigned issues for accurate completion rate
    user_assigned_issues = weekly_data.pop('_user_assigned_issues', [])
    
    # Extract weekly metrics (excluding the special _user_assigned_issues key)
    weekly_completed = [week['completed'] for week in weekly_data.values() if isinstance(week, dict)]
    weekly_started = [week['started'] for week in weekly_data.values() if isinstance(week, dict)]
    weekly_hours = [week['time_spent'] for week in weekly_data.values() if isinstance(week, dict)]
    
    # Calculate completion rate based on all assigned issues
    total_assigned = len(user_assigned_issues)
    total_completed_assigned = sum(1 for issue in user_assigned_issues if issue['completed'])
    
    metrics = {
        'avg_completed_per_week': statistics.mean(weekly_completed) if weekly_completed else 0,
        'avg_started_per_week': statistics.mean(weekly_started) if weekly_started else 0,
        'avg_hours_per_week': statistics.mean(weekly_hours) if weekly_hours else 0,
        'completion_consistency': 1 - (statistics.stdev(weekly_completed) / statistics.mean(weekly_completed)) if len(weekly_completed) > 1 and statistics.mean(weekly_completed) > 0 else 0,
        'total_completed': sum(weekly_completed),
        'total_started': sum(weekly_started),
        'total_hours': sum(weekly_hours),
        'weeks_analyzed': len(weekly_data),
        'total_assigned_issues': total_assigned,
        'total_completed_assigned': total_completed_assigned
    }
    
    # Calculate completion rate based on assigned issues
    if total_assigned > 0:
        metrics['completion_rate'] = total_completed_assigned / total_assigned
    else:
        metrics['completion_rate'] = 0
    
    # Debug output
    print(f"DEBUG: Assigned issues: {total_assigned}, Completed assigned: {total_completed_assigned}, Completion rate: {metrics['completion_rate']:.2%}")
    print(f"DEBUG: Weekly completed: {metrics['total_completed']}, Weekly started: {metrics['total_started']}")
    
    return metrics

def generate_recommendations(metrics, weekly_data):
    """
    Generate personalized recommendations based on performance analysis
    """
    recommendations = []
    insights = []
    
    # Completion rate analysis
    completion_rate = metrics.get('completion_rate', 0)
    if completion_rate >= 0.8:
        insights.append("✅ Excellent completion rate - consistently finishing started work")
    elif completion_rate >= 0.6:
        insights.append("⚠️ Good completion rate - room for improvement in finishing tasks")
        recommendations.append("Focus on completing started tasks before taking on new ones")
    else:
        insights.append("❌ Low completion rate - many tasks started but not finished")
        recommendations.append("Consider reducing work-in-progress and focusing on completion")
        recommendations.append("Review task prioritization and time estimation")
    
    # Workload analysis
    avg_hours = metrics.get('avg_hours_per_week', 0)
    if avg_hours > 45:
        insights.append("⚠️ High workload detected - potential burnout risk")
        recommendations.append("Consider workload redistribution or time management optimization")
    elif avg_hours < 20:
        insights.append("📊 Lower time tracking - may indicate capacity for additional work")
        recommendations.append("Ensure all work is being logged accurately")
    else:
        insights.append("✅ Balanced workload - good time allocation")
    
    # Consistency analysis
    consistency = metrics.get('completion_consistency', 0)
    if consistency < 0.5:
        insights.append("📈 Variable performance pattern detected")
        recommendations.append("Consider establishing more consistent work routines")
        recommendations.append("Review factors causing performance fluctuations")
    else:
        insights.append("✅ Consistent performance pattern")
    
    # Productivity insights
    avg_completed = metrics.get('avg_completed_per_week', 0)
    if avg_completed >= 5:
        insights.append("🚀 High productivity - completing many tasks per week")
    elif avg_completed >= 3:
        insights.append("📊 Good productivity level")
    else:
        insights.append("📈 Opportunity to increase task completion rate")
        recommendations.append("Consider breaking down larger tasks into smaller, manageable pieces")
    
    return {
        'insights': insights,
        'recommendations': recommendations,
        'overall_rating': calculate_overall_rating(metrics)
    }

def calculate_overall_rating(metrics):
    """
    Calculate overall performance rating
    """
    score = 0
    
    # Completion rate (40% weight)
    completion_rate = metrics.get('completion_rate', 0)
    score += completion_rate * 40
    
    # Consistency (30% weight)
    consistency = metrics.get('completion_consistency', 0)
    score += consistency * 30
    
    # Productivity (30% weight)
    avg_completed = metrics.get('avg_completed_per_week', 0)
    productivity_score = min(avg_completed / 5, 1)  # Normalize to 0-1 scale
    score += productivity_score * 30
    
    if score >= 80:
        return "🌟 Excellent"
    elif score >= 65:
        return "✅ Good"
    elif score >= 50:
        return "⚠️ Average"
    else:
        return "❌ Needs Improvement"

def analyze_user_capacity(user_email, weeks_back=8):
    """
    Main function to analyze user capacity and performance
    """
    print(f"\n🔍 Starting capacity analysis for {user_email}")
    print("=" * 60)
    
    # Fetch user issues
    issues = get_user_issues(user_email, weeks_back)
    if not issues:
        return {
            'error': 'No issues found for the specified user',
            'user_email': user_email
        }
    
    # Analyze issue breakdown
    issue_breakdown = analyze_issue_breakdown(issues, user_email)
    
    # Analyze weekly performance
    weekly_data = analyze_weekly_performance(issues, user_email)
    
    # Calculate metrics
    metrics = calculate_performance_metrics(weekly_data)
    
    # Generate recommendations
    recommendations = generate_recommendations(metrics, weekly_data)
    
    # Prepare weekly summary
    weekly_summary = []
    for week_key in sorted(weekly_data.keys()):
        week_data = weekly_data[week_key]
        weekly_summary.append({
            'week': week_key,
            'completed': week_data['completed'],
            'started': week_data['started'],
            'hours_spent': round(week_data['time_spent'], 1),
            'issues_worked': len(week_data['issues'])
        })
    
    # Generate JIRA link for viewing the issues
    start_date = (datetime.now() - timedelta(weeks=weeks_back)).strftime('%Y-%m-%d')
    jql_query = f'assignee = "{user_email}" AND updated >= "{start_date}"'
    
    # URL encode the JQL query
    import urllib.parse
    encoded_jql = urllib.parse.quote(jql_query)
    jira_link = f"{JIRA_URL}/issues/?jql={encoded_jql}"
    
    return {
        'user_email': user_email,
        'analysis_period': f"Last {weeks_back} weeks",
        'metrics': metrics,
        'weekly_summary': weekly_summary,
        'insights': recommendations['insights'],
        'recommendations': recommendations['recommendations'],
        'overall_rating': recommendations['overall_rating'],
        'total_issues_analyzed': len(issues),
        'issue_breakdown': issue_breakdown,
        'jira_link': jira_link,
        'jql_query': jql_query
    }

def analyze_issue_breakdown(issues, user_email):
    """
    Analyze issues by type, priority, and status (only for assigned issues)
    """
    breakdown = {
        'by_type': {},
        'by_priority': {},
        'by_status': {},
        'by_completion': {
            'completed': 0,
            'in_progress': 0,
            'not_started': 0
        },
        'total_issues': len(issues)
    }
    
    for issue in issues:
        fields = issue.get('fields', {})
        
        # Since we only fetch assigned issues, all should be assigned to user
        assignee_email = fields.get('assignee', {}).get('emailAddress', '') if fields.get('assignee') else ''
        if assignee_email != user_email:
            continue
        
        # Issue type breakdown
        issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
        breakdown['by_type'][issue_type] = breakdown['by_type'].get(issue_type, 0) + 1
        
        # Priority breakdown
        priority = fields.get('priority')
        if priority:
            priority_name = priority.get('name', 'Unknown')
        else:
            priority_name = 'No Priority'
        breakdown['by_priority'][priority_name] = breakdown['by_priority'].get(priority_name, 0) + 1
        
        # Status breakdown
        status = fields.get('status', {}).get('name', 'Unknown')
        breakdown['by_status'][status] = breakdown['by_status'].get(status, 0) + 1
        
        # Completion status breakdown
        status_lower = status.lower()
        if status_lower in ['done', 'closed', 'resolved']:
            breakdown['by_completion']['completed'] += 1
        elif status_lower in ['in progress', 'in development', 'in review']:
            breakdown['by_completion']['in_progress'] += 1
        else:
            breakdown['by_completion']['not_started'] += 1
    
    return breakdown

# Only run main if executed directly
if __name__ == "__main__":
    # Example usage
    test_email = "meena.singh@thoughtspot.com"  # Replace with actual email
    result = analyze_user_capacity(test_email)
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n📊 Capacity Analysis for {result['user_email']}")
        print(f"📅 Period: {result['analysis_period']}")
        print(f"📈 Overall Rating: {result['overall_rating']}")
        print(f"📊 Total Issues Analyzed: {result['total_issues_analyzed']}")
        print(f"🔗 View Issues in JIRA: {result['jira_link']}")
        print(f"📝 JQL Query: {result['jql_query']}")
        
        # Issue breakdown
        breakdown = result['issue_breakdown']
        print(f"\n📋 Issue Breakdown:")
        print(f"  📝 By Type:")
        for issue_type, count in sorted(breakdown['by_type'].items(), key=lambda x: x[1], reverse=True):
            print(f"    • {issue_type}: {count}")
        
        print(f"  🚨 By Priority:")
        for priority, count in sorted(breakdown['by_priority'].items(), key=lambda x: x[1], reverse=True):
            print(f"    • {priority}: {count}")
        
        print(f"  ✅ Completion Status:")
        print(f"    • Completed: {breakdown['by_completion']['completed']}")
        print(f"    • In Progress: {breakdown['by_completion']['in_progress']}")
        print(f"    • Not Started: {breakdown['by_completion']['not_started']}")
        
        print(f"\n📋 Key Performance Metrics:")
        print(f"  • Total assigned issues: {result['metrics']['total_assigned_issues']}")
        print(f"  • Completed assigned issues: {result['metrics']['total_completed_assigned']}")
        print(f"  • Completion rate: {result['metrics']['completion_rate']:.1%}")
        print(f"  • Average completed per week: {result['metrics']['avg_completed_per_week']:.1f}")
        print(f"  • Average hours per week: {result['metrics']['avg_hours_per_week']:.1f}")
        
        print(f"\n💡 Insights:")
        for insight in result['insights']:
            print(f"  • {insight}")
        
        print(f"\n🎯 Recommendations:")
        for rec in result['recommendations']:
            print(f"  • {rec}") 