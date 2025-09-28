#!/usr/bin/env python3
"""
Settings Manager Module
Handles application settings, configuration, and user preferences
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import hashlib

class SettingsManager:
    def __init__(self, settings_file: str = 'jira_settings.json'):
        self.settings_file = settings_file
        self.settings_key_file = '.settings_key'
        self.default_settings = {
            'theme': 'light',
            'auto_refresh': True,
            'refresh_interval': 300,  # 5 minutes
            'notifications': {
                'enabled': True,
                'email': True,
                'browser': True
            },
            'dashboard': {
                'default_view': 'overview',
                'show_charts': True,
                'chart_type': 'line'
            },
            'filters': {
                'default_project': '',
                'default_assignee': '',
                'default_status': ''
            },
            'analytics': {
                'enabled': True,
                'tracking_period': 90,
                'show_cost_analysis': True
            },
            'export': {
                'format': 'csv',
                'include_comments': False,
                'include_attachments': False
            },
            'openai_api_key': 'your_openai_api_key_here',
            'azure_openai_endpoint': 'https://your-resource-name.openai.azure.com/',
            'azure_openai_api_version': '2023-05-15',
            'azure_openai_deployment_name': 'gpt-35-turbo',
            'use_azure_openai': False
        }
        self.settings = self.load_settings()
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Merge with default settings to ensure all keys exist
                    merged_settings = self.default_settings.copy()
                    merged_settings.update(settings)
                    return merged_settings
            else:
                return self.default_settings.copy()
        except Exception as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value"""
        keys = key.split('.')
        value = self.settings
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set_setting(self, key: str, value: Any) -> bool:
        """Set a specific setting value"""
        try:
            keys = key.split('.')
            current = self.settings
            
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            
            current[keys[-1]] = value
            return self.save_settings()
        except Exception as e:
            print(f"Error setting value: {e}")
            return False
    
    def update_jira_credentials(self, jira_url: str, jira_email: str, jira_token: str) -> bool:
        """Update Jira credentials"""
        try:
            self.settings['jira_url'] = jira_url
            self.settings['jira_email'] = jira_email
            self.settings['jira_token'] = jira_token
            return self.save_settings()
        except Exception as e:
            print(f"Error updating Jira credentials: {e}")
            return False
    
    def get_jira_credentials(self) -> Dict[str, str]:
        """Get Jira credentials - prioritize environment variables over stored settings"""
        # First check environment variables
        env_url = os.getenv('JIRA_URL', '')
        env_email = os.getenv('JIRA_EMAIL', '')
        env_token = os.getenv('JIRA_API_TOKEN', '')
        
        # Use environment variables if available, otherwise fall back to stored settings
        jira_url = env_url if env_url else self.settings.get('jira_url', '')
        jira_email = env_email if env_email else self.settings.get('jira_email', '')
        jira_token = env_token if env_token else self.settings.get('jira_token', '')
        
        return {
            'url': jira_url,
            'email': jira_email,
            'api_token': jira_token,
            # Legacy keys for backward compatibility
            'jira_url': jira_url,
            'jira_email': jira_email,
            'jira_token': jira_token
        }
    
    def validate_jira_credentials(self) -> bool:
        """Validate if Jira credentials are set"""
        creds = self.get_jira_credentials()
        return all([creds['jira_url'], creds['jira_email'], creds['jira_token']])
    
    def has_valid_credentials(self) -> bool:
        """Check if valid Jira credentials are configured"""
        return self.validate_jira_credentials()
    
    def save_jira_settings(self, url: str, email: str, token: str) -> bool:
        """Save Jira settings (legacy method for app.py compatibility)"""
        return self.update_jira_credentials(url, email, token)
    
    def get_masked_settings(self) -> Dict[str, Any]:
        """Get settings with sensitive data masked"""
        settings = self.get_all_settings()
        if 'jira_token' in settings:
            settings['jira_token'] = '*' * 8 if settings['jira_token'] else ''
        return settings
    
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is configured"""
        key = self.get_setting('openai_api_key', '')
        # Check if key exists and is not a placeholder
        if not key or len(key) < 20:
            return False
        # Check for common placeholder patterns
        if 'QRSTUVWXYZ' in key or '1234567890' in key:
            return False
        return True
    
    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration"""
        return {
            'api_key': self.get_setting('openai_api_key', ''),
            'azure_endpoint': self.get_setting('azure_openai_endpoint', ''),
            'azure_api_version': self.get_setting('azure_openai_api_version', '2023-05-15'),
            'azure_deployment_name': self.get_setting('azure_openai_deployment_name', 'gpt-35-turbo'),
            'use_azure': self.get_setting('use_azure_openai', True)
        }
    
    def update_openai_config(self, config: Dict[str, Any]) -> bool:
        """Update OpenAI configuration"""
        try:
            if 'api_key' in config:
                self.set_setting('openai_api_key', config['api_key'])
            if 'azure_endpoint' in config:
                self.set_setting('azure_openai_endpoint', config['azure_endpoint'])
            if 'azure_api_version' in config:
                self.set_setting('azure_openai_api_version', config['azure_api_version'])
            if 'azure_deployment_name' in config:
                self.set_setting('azure_openai_deployment_name', config['azure_deployment_name'])
            if 'use_azure' in config:
                self.set_setting('use_azure_openai', config['use_azure'])
            return self.save_settings()
        except Exception as e:
            print(f"Error updating OpenAI config: {e}")
            return False
    
    def save_setting(self, key: str, value: Any, encrypt: bool = False) -> bool:
        """Save a setting with optional encryption"""
        # For now, we'll store as plain text
        # In production, you'd want to implement actual encryption
        return self.set_setting(key, value)
    
    def update_theme(self, theme: str) -> bool:
        """Update application theme"""
        if theme in ['light', 'dark', 'auto']:
            return self.set_setting('theme', theme)
        return False
    
    def get_theme(self) -> str:
        """Get current theme"""
        return self.get_setting('theme', 'light')
    
    def update_dashboard_settings(self, dashboard_settings: Dict[str, Any]) -> bool:
        """Update dashboard settings"""
        try:
            current_dashboard = self.get_setting('dashboard', {})
            current_dashboard.update(dashboard_settings)
            return self.set_setting('dashboard', current_dashboard)
        except Exception as e:
            print(f"Error updating dashboard settings: {e}")
            return False
    
    def get_dashboard_settings(self) -> Dict[str, Any]:
        """Get dashboard settings"""
        return self.get_setting('dashboard', self.default_settings['dashboard'])
    
    def update_notification_settings(self, notification_settings: Dict[str, Any]) -> bool:
        """Update notification settings"""
        try:
            current_notifications = self.get_setting('notifications', {})
            current_notifications.update(notification_settings)
            return self.set_setting('notifications', current_notifications)
        except Exception as e:
            print(f"Error updating notification settings: {e}")
            return False
    
    def get_notification_settings(self) -> Dict[str, Any]:
        """Get notification settings"""
        return self.get_setting('notifications', self.default_settings['notifications'])
    
    def update_analytics_settings(self, analytics_settings: Dict[str, Any]) -> bool:
        """Update analytics settings"""
        try:
            current_analytics = self.get_setting('analytics', {})
            current_analytics.update(analytics_settings)
            return self.set_setting('analytics', current_analytics)
        except Exception as e:
            print(f"Error updating analytics settings: {e}")
            return False
    
    def get_analytics_settings(self) -> Dict[str, Any]:
        """Get analytics settings"""
        return self.get_setting('analytics', self.default_settings['analytics'])
    
    def export_settings(self) -> str:
        """Export settings as JSON string"""
        try:
            # Remove sensitive data
            export_settings = self.settings.copy()
            export_settings.pop('jira_token', None)
            return json.dumps(export_settings, indent=2)
        except Exception as e:
            print(f"Error exporting settings: {e}")
            return "{}"
    
    def import_settings(self, settings_json: str) -> bool:
        """Import settings from JSON string"""
        try:
            imported_settings = json.loads(settings_json)
            # Merge with current settings
            self.settings.update(imported_settings)
            return self.save_settings()
        except Exception as e:
            print(f"Error importing settings: {e}")
            return False
    
    def reset_settings(self) -> bool:
        """Reset settings to default"""
        try:
            self.settings = self.default_settings.copy()
            return self.save_settings()
        except Exception as e:
            print(f"Error resetting settings: {e}")
            return False
    
    def generate_settings_key(self) -> str:
        """Generate a unique settings key"""
        timestamp = str(datetime.now().timestamp())
        user_data = f"{self.settings.get('jira_email', '')}{timestamp}"
        return hashlib.md5(user_data.encode()).hexdigest()
    
    def save_settings_key(self) -> bool:
        """Save settings key to file"""
        try:
            key = self.generate_settings_key()
            with open(self.settings_key_file, 'w') as f:
                f.write(key)
            return True
        except Exception as e:
            print(f"Error saving settings key: {e}")
            return False
    
    def load_settings_key(self) -> Optional[str]:
        """Load settings key from file"""
        try:
            if os.path.exists(self.settings_key_file):
                with open(self.settings_key_file, 'r') as f:
                    return f.read().strip()
            return None
        except Exception as e:
            print(f"Error loading settings key: {e}")
            return None
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get all settings"""
        return self.settings.copy()
    
    def backup_settings(self, backup_file: str = None) -> bool:
        """Create a backup of current settings"""
        try:
            if backup_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f"settings_backup_{timestamp}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
            
            print(f"Settings backed up to: {backup_file}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_settings(self, backup_file: str) -> bool:
        """Restore settings from backup file"""
        try:
            if os.path.exists(backup_file):
                with open(backup_file, 'r', encoding='utf-8') as f:
                    backup_settings = json.load(f)
                
                self.settings = backup_settings
                return self.save_settings()
            else:
                print(f"Backup file not found: {backup_file}")
                return False
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False

# Global settings manager instance
settings_manager = SettingsManager()
