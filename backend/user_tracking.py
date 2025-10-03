"""
User Tracking Module for JIRA TPM Application
Tracks users by IP address and cookies for analytics purposes
"""

import sqlite3
import json
import hashlib
import uuid
from datetime import datetime, timedelta
from flask import request, session, g
import logging
import os
from typing import Dict, List, Optional, Tuple
import threading

logger = logging.getLogger(__name__)

class UserTracker:
    def __init__(self, db_path: str = "user_tracking.db"):
        """Initialize the user tracker with SQLite database"""
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_database()
    
    def init_database(self):
        """Initialize the SQLite database with required tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_sessions INTEGER DEFAULT 1,
                    total_page_views INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create sessions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT NOT NULL,
                    ip_address TEXT NOT NULL,
                    user_agent TEXT,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    duration_seconds INTEGER,
                    page_views INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create page_views table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS page_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    page_path TEXT NOT NULL,
                    page_title TEXT,
                    referrer TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    load_time_ms INTEGER,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create events table for custom tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (session_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_ip ON users(ip_address)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_last_seen ON users(last_seen)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_page_views_session_id ON page_views(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_session_id ON events(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type)')
            
            conn.commit()
            conn.close()
            logger.info("User tracking database initialized successfully")
    
    def get_client_ip(self) -> str:
        """Get the client's IP address, considering proxies"""
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr
    
    def generate_user_id(self, ip_address: str, user_agent: str = "") -> str:
        """Generate a unique user ID based on IP and user agent"""
        # Create a hash of IP + user agent for consistent user identification
        combined = f"{ip_address}:{user_agent}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def get_or_create_user(self, ip_address: str, user_agent: str = "") -> Tuple[str, bool]:
        """Get existing user or create new one. Returns (user_id, is_new_user)"""
        user_id = self.generate_user_id(ip_address, user_agent)
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                # Update last seen and increment sessions
                cursor.execute('''
                    UPDATE users 
                    SET last_seen = CURRENT_TIMESTAMP, 
                        total_sessions = total_sessions + 1,
                        is_active = 1
                    WHERE user_id = ?
                ''', (user_id,))
                is_new_user = False
            else:
                # Create new user
                cursor.execute('''
                    INSERT INTO users (user_id, ip_address, user_agent, first_seen, last_seen)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (user_id, ip_address, user_agent))
                is_new_user = True
            
            conn.commit()
            conn.close()
            
            return user_id, is_new_user
    
    def start_session(self, user_id: str, ip_address: str, user_agent: str = "") -> str:
        """Start a new session and return session ID"""
        session_id = str(uuid.uuid4())
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sessions (session_id, user_id, ip_address, user_agent, start_time)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (session_id, user_id, ip_address, user_agent))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Started new session {session_id} for user {user_id}")
            return session_id
    
    def end_session(self, session_id: str):
        """End a session and calculate duration"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get session start time
            cursor.execute('SELECT start_time FROM sessions WHERE session_id = ?', (session_id,))
            result = cursor.fetchone()
            
            if result:
                # Parse datetime string (compatible with Python 3.6)
                start_time_str = result[0]
                if 'T' in start_time_str:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S.%f')
                else:
                    start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
                end_time = datetime.now()
                duration = int((end_time - start_time).total_seconds())
                
                cursor.execute('''
                    UPDATE sessions 
                    SET end_time = CURRENT_TIMESTAMP, duration_seconds = ?
                    WHERE session_id = ?
                ''', (duration, session_id))
                
                conn.commit()
                logger.info(f"Ended session {session_id} with duration {duration} seconds")
            
            conn.close()
    
    def track_page_view(self, session_id: str, user_id: str, page_path: str, 
                       page_title: str = "", referrer: str = "", load_time_ms: int = 0):
        """Track a page view"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Insert page view
            cursor.execute('''
                INSERT INTO page_views (session_id, user_id, page_path, page_title, referrer, load_time_ms)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_id, page_path, page_title, referrer, load_time_ms))
            
            # Update session page view count
            cursor.execute('''
                UPDATE sessions SET page_views = page_views + 1 WHERE session_id = ?
            ''', (session_id,))
            
            # Update user total page views
            cursor.execute('''
                UPDATE users SET total_page_views = total_page_views + 1 WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
    
    def track_event(self, session_id: str, user_id: str, event_type: str, event_data: Dict = None):
        """Track a custom event"""
        event_data_json = json.dumps(event_data) if event_data else None
        
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO events (session_id, user_id, event_type, event_data)
                VALUES (?, ?, ?, ?)
            ''', (session_id, user_id, event_type, event_data_json))
            
            conn.commit()
            conn.close()
    
    def get_user_stats(self, days: int = 30) -> Dict:
        """Get user statistics for the last N days"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total users
            cursor.execute('SELECT COUNT(*) FROM users')
            total_users = cursor.fetchone()[0]
            
            # Active users (last 24 hours)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_seen > datetime('now', '-1 day')
            ''')
            active_users_24h = cursor.fetchone()[0]
            
            # Active users (last 7 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_seen > datetime('now', '-7 days')
            ''')
            active_users_7d = cursor.fetchone()[0]
            
            # Active users (last 30 days)
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE last_seen > datetime('now', '-30 days')
            ''')
            active_users_30d = cursor.fetchone()[0]
            
            # New users today
            cursor.execute('''
                SELECT COUNT(*) FROM users 
                WHERE date(first_seen) = date('now')
            ''')
            new_users_today = cursor.fetchone()[0]
            
            # Total sessions
            cursor.execute('SELECT COUNT(*) FROM sessions')
            total_sessions = cursor.fetchone()[0]
            
            # Total page views
            cursor.execute('SELECT COUNT(*) FROM page_views')
            total_page_views = cursor.fetchone()[0]
            
            # Average session duration
            cursor.execute('''
                SELECT AVG(duration_seconds) FROM sessions 
                WHERE duration_seconds IS NOT NULL
            ''')
            avg_session_duration = cursor.fetchone()[0] or 0
            
            # Top pages
            cursor.execute('''
                SELECT page_path, COUNT(*) as views 
                FROM page_views 
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY page_path 
                ORDER BY views DESC 
                LIMIT 10
            ''')
            top_pages = [{'page': row[0], 'views': row[1]} for row in cursor.fetchall()]
            
            # Daily active users for the last 30 days
            cursor.execute('''
                SELECT date(last_seen) as date, COUNT(DISTINCT user_id) as users
                FROM users 
                WHERE last_seen > datetime('now', '-30 days')
                GROUP BY date(last_seen)
                ORDER BY date(last_seen)
            ''')
            daily_active_users = [{'date': row[0], 'users': row[1]} for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'total_users': total_users,
                'active_users_24h': active_users_24h,
                'active_users_7d': active_users_7d,
                'active_users_30d': active_users_30d,
                'new_users_today': new_users_today,
                'total_sessions': total_sessions,
                'total_page_views': total_page_views,
                'avg_session_duration': round(avg_session_duration, 2),
                'top_pages': top_pages,
                'daily_active_users': daily_active_users
            }
    
    def get_user_details(self, user_id: str) -> Dict:
        """Get detailed information about a specific user"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # User basic info
            cursor.execute('''
                SELECT user_id, ip_address, user_agent, first_seen, last_seen, 
                       total_sessions, total_page_views, is_active
                FROM users WHERE user_id = ?
            ''', (user_id,))
            user_info = cursor.fetchone()
            
            if not user_info:
                conn.close()
                return None
            
            # User sessions
            cursor.execute('''
                SELECT session_id, start_time, end_time, duration_seconds, page_views
                FROM sessions WHERE user_id = ? ORDER BY start_time DESC
            ''', (user_id,))
            sessions = [{
                'session_id': row[0],
                'start_time': row[1],
                'end_time': row[2],
                'duration_seconds': row[3],
                'page_views': row[4]
            } for row in cursor.fetchall()]
            
            # Recent page views
            cursor.execute('''
                SELECT page_path, page_title, timestamp, load_time_ms
                FROM page_views WHERE user_id = ? 
                ORDER BY timestamp DESC LIMIT 20
            ''', (user_id,))
            recent_views = [{
                'page_path': row[0],
                'page_title': row[1],
                'timestamp': row[2],
                'load_time_ms': row[3]
            } for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'user_id': user_info[0],
                'ip_address': user_info[1],
                'user_agent': user_info[2],
                'first_seen': user_info[3],
                'last_seen': user_info[4],
                'total_sessions': user_info[5],
                'total_page_views': user_info[6],
                'is_active': user_info[7],
                'sessions': sessions,
                'recent_page_views': recent_views
            }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """Clean up old tracking data to keep database size manageable"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # Delete old page views
            cursor.execute('''
                DELETE FROM page_views 
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            # Delete old events
            cursor.execute('''
                DELETE FROM events 
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            # Delete old sessions
            cursor.execute('''
                DELETE FROM sessions 
                WHERE start_time < ?
            ''', (cutoff_date,))
            
            # Mark old users as inactive
            cursor.execute('''
                UPDATE users 
                SET is_active = 0 
                WHERE last_seen < ?
            ''', (cutoff_date,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up tracking data older than {days_to_keep} days")

# Global tracker instance
tracker = UserTracker()

def track_user_request():
    """Middleware function to track user requests"""
    try:
        ip_address = tracker.get_client_ip()
        user_agent = request.headers.get('User-Agent', '')
        
        # Get or create user
        user_id, is_new_user = tracker.get_or_create_user(ip_address, user_agent)
        
        # Get or create session
        session_id = session.get('tracking_session_id')
        if not session_id:
            session_id = tracker.start_session(user_id, ip_address, user_agent)
            session['tracking_session_id'] = session_id
            session['tracking_user_id'] = user_id
        
        # Store in Flask g for use in route handlers
        g.tracking_user_id = user_id
        g.tracking_session_id = session_id
        g.tracking_is_new_user = is_new_user
        
        logger.debug(f"Tracking request: user_id={user_id}, session_id={session_id}, is_new={is_new_user}")
        
    except Exception as e:
        logger.error(f"Error in user tracking: {str(e)}")

def track_page_view(page_path: str, page_title: str = "", referrer: str = "", load_time_ms: int = 0):
    """Track a page view for the current user"""
    try:
        if hasattr(g, 'tracking_session_id') and hasattr(g, 'tracking_user_id'):
            tracker.track_page_view(
                g.tracking_session_id,
                g.tracking_user_id,
                page_path,
                page_title,
                referrer,
                load_time_ms
            )
    except Exception as e:
        logger.error(f"Error tracking page view: {str(e)}")

def track_event(event_type: str, event_data: Dict = None):
    """Track a custom event for the current user"""
    try:
        if hasattr(g, 'tracking_session_id') and hasattr(g, 'tracking_user_id'):
            tracker.track_event(g.tracking_session_id, g.tracking_user_id, event_type, event_data)
    except Exception as e:
        logger.error(f"Error tracking event: {str(e)}")
