#!/usr/bin/env python3
"""
AI Sprint Insights Module
Provides AI-powered analysis and insights for sprint planning and execution
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import requests
import openai
import os
import logging

class AISprintInsights:
    def __init__(self, jira_url: str, jira_email: str, jira_token: str):
        self.jira_url = jira_url
        self.jira_email = jira_email
        self.jira_token = jira_token
        self.headers = self._get_headers()
        self._setup_openai()
    
    def _setup_openai(self):
        """Setup OpenAI client with Azure configuration"""
        try:
            # Import settings manager to get OpenAI config
            from settings_manager import SettingsManager
            settings = SettingsManager()
            config = settings.get_openai_config()
            
            if config['use_azure']:
                # Azure OpenAI configuration
                from openai import AzureOpenAI
                self.client = AzureOpenAI(
                    api_key=config['api_key'],
                    api_version=config['azure_api_version'],
                    azure_endpoint=config['azure_endpoint']
                )
                self.deployment_name = config['azure_deployment_name']
                self.use_azure = True
            else:
                # Standard OpenAI configuration
                from openai import OpenAI
                self.client = OpenAI(api_key=config['api_key'])
                self.use_azure = False
                
            self.openai_configured = bool(config['api_key']) and len(config['api_key']) > 20
        except Exception as e:
            print(f"Error setting up OpenAI: {e}")
            self.openai_configured = False
            self.use_azure = False
            self.client = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate headers for Jira API requests"""
        import base64
        auth_string = f"{self.jira_email}:{self.jira_token}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        
        return {
            'Authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def analyze_sprint_performance(self, sprint_id: str) -> Dict[str, Any]:
        """Analyze sprint performance with AI insights"""
        try:
            sprint_data = self._get_sprint_data(sprint_id)
            if not sprint_data:
                return {'error': 'Sprint not found'}
            
            # Try to get AI insights first
            ai_insights = self._get_ai_insights(sprint_data)

            if ai_insights:
                # Use AI insights
                return ai_insights
            else:
                insights = {
                    'overall_assessment': 'Sprint analysis completed using rule-based approach.',
                    'insights': [],
                    'key_observations': [],
                    'recommendations': self._generate_recommendations(sprint_data),
                    'fallback': True
                }
                # Add basic analysis
                sprint_summary = self._get_sprint_summary(sprint_data)
                velocity = self._analyze_velocity(sprint_data)
                risks = self._assess_risks(sprint_data)
                # Generate insights based on analysis
                if sprint_summary['completion_rate'] > 80:
                    insights['insights'].append({
                        'title': 'High Performance',
                        'description': 'Team is performing well with high completion rates.',
                        'category': 'Execution',
                        'impact': 'High'
                    })
                elif sprint_summary['completion_rate'] > 60:
                    insights['insights'].append({
                        'title': 'Moderate Performance',
                        'description': 'Team performance is moderate. Consider identifying blockers.',
                        'category': 'Execution',
                        'impact': 'Medium'
                    })
                else:
                    insights['insights'].append({
                        'title': 'Performance Concerns',
                        'description': 'Low completion rate indicates potential issues that need attention.',
                        'category': 'Execution',
                        'impact': 'High'
                    })
                insights['key_observations'] = [
                    f"Sprint: {sprint_summary['sprint_name']}",
                    f"Completion rate: {sprint_summary['completion_rate']:.1f}%",
                    f"Total issues: {sprint_summary['total_issues']}",
                    f"Risk level: {risks['risk_level']}"
                ]
                return insights
        except Exception as e:
            print(f"Error analyzing sprint performance: {e}")
            return {'error': str(e)}
    
    def predict_sprint_outcome(self, sprint_id: str) -> Dict[str, Any]:
        """Predict sprint outcome based on current progress"""
        try:
            sprint_data = self._get_sprint_data(sprint_id)
            if not sprint_data:
                return {'error': 'Sprint not found'}
            
            prediction = {
                'completion_probability': self._calculate_completion_probability(sprint_data),
                'estimated_completion_date': self._estimate_completion_date(sprint_data),
                'at_risk_issues': self._identify_at_risk_issues(sprint_data),
                'resource_recommendations': self._recommend_resources(sprint_data)
            }
            
            return prediction
        except Exception as e:
            print(f"Error predicting sprint outcome: {e}")
            return {'error': str(e)}
    
    def _get_sprint_data(self, sprint_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive sprint data from Jira"""
        try:
            sprint_url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}"
            response = requests.get(sprint_url, headers=self.headers)
            
            if response.status_code == 200:
                sprint_info = response.json()
                
                # Get sprint issues
                issues_url = f"{self.jira_url}/rest/agile/1.0/sprint/{sprint_id}/issue"
                issues_response = requests.get(issues_url, headers=self.headers)
                
                if issues_response.status_code == 200:
                    issues_data = issues_response.json()
                    sprint_info['issues'] = issues_data.get('issues', [])
                
                return sprint_info
            else:
                return None
        except Exception as e:
            print(f"Error getting sprint data: {e}")
            return None
    
    def _get_sprint_summary(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sprint summary"""
        issues = sprint_data.get('issues', [])
        
        total_issues = len(issues)
        completed_issues = len([i for i in issues if i.get('fields', {}).get('status', {}).get('name') == 'Done'])
        in_progress_issues = len([i for i in issues if i.get('fields', {}).get('status', {}).get('name') == 'In Progress'])
        
        return {
            'total_issues': total_issues,
            'completed_issues': completed_issues,
            'in_progress_issues': in_progress_issues,
            'completion_rate': (completed_issues / total_issues * 100) if total_issues > 0 else 0,
            'sprint_name': sprint_data.get('name', 'Unknown Sprint'),
            'sprint_state': sprint_data.get('state', 'Unknown')
        }
    
    def _analyze_velocity(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team velocity"""
        issues = sprint_data.get('issues', [])
        
        total_story_points = 0
        completed_story_points = 0
        
        for issue in issues:
            story_points = issue.get('fields', {}).get('customfield_10016', 0) or 0
            total_story_points += story_points
            
            if issue.get('fields', {}).get('status', {}).get('name') == 'Done':
                completed_story_points += story_points
        
        return {
            'total_story_points': total_story_points,
            'completed_story_points': completed_story_points,
            'velocity_percentage': (completed_story_points / total_story_points * 100) if total_story_points > 0 else 0,
            'projected_velocity': completed_story_points * 1.1  # 10% buffer
        }
    
    def _analyze_burndown(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze burndown chart trends"""
        # Mock burndown analysis
        return {
            'trend': 'decreasing',
            'ideal_burndown': [100, 80, 60, 40, 20, 0],
            'actual_burndown': [100, 85, 70, 45, 25, 10],
            'burndown_health': 'good'
        }
    
    def _analyze_team_performance(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze team performance metrics"""
        issues = sprint_data.get('issues', [])
        
        assignee_performance = {}
        for issue in issues:
            assignee = issue.get('fields', {}).get('assignee', {})
            if assignee:
                assignee_name = assignee.get('displayName', 'Unassigned')
                if assignee_name not in assignee_performance:
                    assignee_performance[assignee_name] = {'total': 0, 'completed': 0}
                
                assignee_performance[assignee_name]['total'] += 1
                if issue.get('fields', {}).get('status', {}).get('name') == 'Done':
                    assignee_performance[assignee_name]['completed'] += 1
        
        return {
            'team_members': len(assignee_performance),
            'individual_performance': assignee_performance,
            'team_collaboration_score': 85  # Mock score
        }
    
    def _assess_risks(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess sprint risks"""
        issues = sprint_data.get('issues', [])
        
        high_priority_issues = len([i for i in issues if i.get('fields', {}).get('priority', {}).get('name') == 'High'])
        blocked_issues = len([i for i in issues if 'blocked' in str(i.get('fields', {}).get('status', {}).get('name', '')).lower()])
        
        risk_level = 'Low'
        if high_priority_issues > 3 or blocked_issues > 1:
            risk_level = 'High'
        elif high_priority_issues > 1 or blocked_issues > 0:
            risk_level = 'Medium'
        
        return {
            'risk_level': risk_level,
            'high_priority_issues': high_priority_issues,
            'blocked_issues': blocked_issues,
            'risk_factors': [
                'High priority issues pending',
                'Blocked issues present'
            ] if risk_level != 'Low' else []
        }
    
    def _generate_recommendations(self, sprint_data: Dict[str, Any]) -> List[str]:
        """Generate AI-powered recommendations"""
        recommendations = []
        
        sprint_summary = self._get_sprint_summary(sprint_data)
        velocity = self._analyze_velocity(sprint_data)
        risks = self._assess_risks(sprint_data)
        
        if sprint_summary['completion_rate'] < 50:
            recommendations.append("Consider reducing scope or extending sprint duration")
        
        if velocity['velocity_percentage'] < 70:
            recommendations.append("Team velocity is below target - investigate blockers")
        
        if risks['risk_level'] == 'High':
            recommendations.append("Address high-priority and blocked issues immediately")
        
        if sprint_summary['in_progress_issues'] > sprint_summary['completed_issues']:
            recommendations.append("Focus on completing in-progress items before starting new work")
        
        return recommendations
    
    def _calculate_completion_probability(self, sprint_data: Dict[str, Any]) -> float:
        """Calculate probability of sprint completion"""
        velocity = self._analyze_velocity(sprint_data)
        risks = self._assess_risks(sprint_data)
        
        base_probability = velocity['velocity_percentage']
        
        # Adjust based on risk level
        if risks['risk_level'] == 'High':
            base_probability *= 0.7
        elif risks['risk_level'] == 'Medium':
            base_probability *= 0.85
        
        return min(base_probability, 100)
    
    def _estimate_completion_date(self, sprint_data: Dict[str, Any]) -> str:
        """Estimate sprint completion date"""
        # Mock estimation based on current progress
        current_date = datetime.now()
        estimated_date = current_date + timedelta(days=3)
        return estimated_date.strftime('%Y-%m-%d')
    
    def _identify_at_risk_issues(self, sprint_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify issues at risk of not completing"""
        issues = sprint_data.get('issues', [])
        at_risk = []
        
        for issue in issues:
            if (issue.get('fields', {}).get('priority', {}).get('name') == 'High' and
                issue.get('fields', {}).get('status', {}).get('name') != 'Done'):
                at_risk.append({
                    'key': issue.get('key'),
                    'summary': issue.get('fields', {}).get('summary', ''),
                    'priority': issue.get('fields', {}).get('priority', {}).get('name', ''),
                    'status': issue.get('fields', {}).get('status', {}).get('name', '')
                })
        
        return at_risk
    
    def _recommend_resources(self, sprint_data: Dict[str, Any]) -> List[str]:
        """Recommend resource allocation"""
        return [
            "Consider adding senior developer to high-priority items",
            "Pair programming recommended for complex tasks",
            "Schedule daily standups to address blockers quickly"
        ]
    
    def _get_ai_insights(self, sprint_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get AI-powered insights using OpenAI"""
        if not self.openai_configured or not self.client:
            return None
            
        try:
            # Prepare sprint data summary for AI analysis
            summary = self._prepare_sprint_summary_for_ai(sprint_data)
            
            prompt = f"""
            Analyze the following sprint data and provide insights:
            
            {summary}
            
            Please provide:
            1. Overall assessment of sprint performance
            2. Key insights about team performance, velocity, and execution
            3. Specific recommendations for improvement
            4. Risk assessment and mitigation strategies
            
            Format your response as JSON with the following structure:
            {{
                "overall_assessment": "string",
                "insights": [
                    {{
                        "title": "string",
                        "description": "string",
                        "category": "Planning|Execution|Team|Process",
                        "impact": "High|Medium|Low"
                    }}
                ],
                "key_observations": ["string1", "string2", ...],
                "recommendations": ["string1", "string2", ...]
            }}
            
            Respond ONLY with valid JSON. Do not include any text before or after the JSON.
            """
            
            if self.use_azure:
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": "You are an expert Agile coach and sprint analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
            else:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini-2024-07-18",
                    messages=[
                        {"role": "system", "content": "You are an expert Agile coach and sprint analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=1000,
                    temperature=0.7
                )
            
            # Print the entire OpenAI response object for debugging
            print(f"Full OpenAI response object: {response}")
            ai_response = None
            # Try to extract the content safely
            try:
                ai_response = response.choices[0].message.content
            except Exception as e:
                print(f"Error extracting message content from OpenAI response: {e}")
            if not ai_response or not ai_response.strip():
                print("OpenAI response content is empty or missing. Returning fallback.")
                return {
                    'overall_assessment': 'OpenAI response was empty or invalid.',
                    'insights': [],
                    'key_observations': [],
                    'recommendations': [],
                    'fallback': True,
                    'raw_openai_response': str(response)
                }
            print(f"Raw OpenAI response: {ai_response}")
            try:
                return json.loads(ai_response)
            except Exception as e:
                print(f"Error parsing OpenAI response as JSON: {e}")
                return {
                    'overall_assessment': 'OpenAI response was not valid JSON.',
                    'insights': [],
                    'key_observations': [],
                    'recommendations': [],
                    'fallback': True,
                    'raw_openai_response': ai_response
                }
            
        except Exception as e:
            print(f"Error getting AI insights: {e}")
            return None
    
    def _prepare_sprint_summary_for_ai(self, sprint_data: Dict[str, Any]) -> str:
        """Prepare sprint data summary for AI analysis"""
        summary = f"Sprint: {sprint_data.get('name', 'Unknown')}\n"
        summary += f"State: {sprint_data.get('state', 'Unknown')}\n"
        
        issues = sprint_data.get('issues', [])
        if issues:
            summary += f"Total Issues: {len(issues)}\n"
            
            # Count by status
            status_counts = {}
            for issue in issues:
                status = issue.get('fields', {}).get('status', {}).get('name', 'Unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            summary += "Issue Status Distribution:\n"
            for status, count in status_counts.items():
                summary += f"  {status}: {count}\n"
            
            # Count by priority
            priority_counts = {}
            for issue in issues:
                priority = issue.get('fields', {}).get('priority', {}).get('name', 'Unknown')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
            
            summary += "Priority Distribution:\n"
            for priority, count in priority_counts.items():
                summary += f"  {priority}: {count}\n"
        
        return summary
