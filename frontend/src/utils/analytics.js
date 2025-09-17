/**
 * Analytics tracking utility for the JIRA TPM application
 * Tracks user interactions, page views, and custom events
 */

import axios from 'axios';

class Analytics {
  constructor() {
    this.sessionId = this.getOrCreateSessionId();
    this.startTime = Date.now();
    this.pageLoadTime = 0;
    this.isTrackingEnabled = true;
    
    // Track initial page load
    this.trackPageLoad();
    
    // Track page visibility changes
    this.setupVisibilityTracking();
    
    // Track before page unload
    this.setupUnloadTracking();
  }

  getOrCreateSessionId() {
    let sessionId = sessionStorage.getItem('analytics_session_id');
    if (!sessionId) {
      sessionId = this.generateSessionId();
      sessionStorage.setItem('analytics_session_id', sessionId);
    }
    return sessionId;
  }

  generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  }

  trackPageLoad() {
    if (!this.isTrackingEnabled) return;
    
    const pagePath = window.location.pathname;
    const pageTitle = document.title;
    const referrer = document.referrer;
    
    // Calculate page load time
    window.addEventListener('load', () => {
      this.pageLoadTime = Date.now() - this.startTime;
      this.trackPageView(pagePath, pageTitle, referrer, this.pageLoadTime);
    });
  }

  trackPageView(pagePath, pageTitle = '', referrer = '', loadTimeMs = 0) {
    if (!this.isTrackingEnabled) return;
    
    const data = {
      page_path: pagePath,
      page_title: pageTitle,
      referrer: referrer,
      load_time_ms: loadTimeMs
    };

    this.sendToBackend('/api/analytics/pageview', data)
      .catch(error => {
        console.warn('Failed to track page view:', error);
      });
  }

  trackEvent(eventType, eventData = {}) {
    if (!this.isTrackingEnabled) return;
    
    const data = {
      event_type: eventType,
      event_data: {
        ...eventData,
        timestamp: new Date().toISOString(),
        session_id: this.sessionId,
        user_agent: navigator.userAgent,
        screen_resolution: `${screen.width}x${screen.height}`,
        viewport_size: `${window.innerWidth}x${window.innerHeight}`,
        language: navigator.language,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
      }
    };

    this.sendToBackend('/api/analytics/track', data)
      .catch(error => {
        console.warn('Failed to track event:', error);
      });
  }

  trackUserInteraction(action, target, details = {}) {
    this.trackEvent('user_interaction', {
      action,
      target,
      ...details
    });
  }

  trackFeatureUsage(feature, details = {}) {
    this.trackEvent('feature_used', {
      feature,
      ...details
    });
  }

  trackError(error, context = {}) {
    this.trackEvent('error_occurred', {
      error_message: error.message || error,
      error_stack: error.stack,
      context,
      url: window.location.href
    });
  }

  trackPerformance(metric, value, details = {}) {
    this.trackEvent('performance_metric', {
      metric,
      value,
      ...details
    });
  }

  setupVisibilityTracking() {
    let visibilityStartTime = Date.now();
    
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        // Page became hidden, track time spent
        const timeSpent = Date.now() - visibilityStartTime;
        this.trackEvent('page_visibility', {
          action: 'hidden',
          time_spent_ms: timeSpent
        });
      } else {
        // Page became visible, reset timer
        visibilityStartTime = Date.now();
        this.trackEvent('page_visibility', {
          action: 'visible'
        });
      }
    });
  }

  setupUnloadTracking() {
    window.addEventListener('beforeunload', () => {
      // Track session end
      const sessionDuration = Date.now() - this.startTime;
      this.trackEvent('session_end', {
        session_duration_ms: sessionDuration,
        page_load_time_ms: this.pageLoadTime
      });
    });
  }

  async sendToBackend(endpoint, data) {
    try {
      const response = await axios.post(endpoint, data, {
        timeout: 5000, // 5 second timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      // Don't throw errors for analytics failures
      console.warn('Analytics request failed:', error);
      throw error;
    }
  }

  // Utility methods for common tracking scenarios
  trackButtonClick(buttonName, location = '') {
    this.trackUserInteraction('button_click', buttonName, { location });
  }

  trackFormSubmit(formName, success = true) {
    this.trackUserInteraction('form_submit', formName, { success });
  }

  trackNavigation(from, to) {
    this.trackEvent('navigation', { from, to });
  }

  trackSearch(query, resultsCount = 0) {
    this.trackEvent('search_performed', { 
      query, 
      results_count: resultsCount 
    });
  }

  trackDownload(fileName, fileType = '') {
    this.trackEvent('file_download', { 
      file_name: fileName, 
      file_type: fileType 
    });
  }

  trackShare(method, content = '') {
    this.trackEvent('content_shared', { 
      method, 
      content 
    });
  }

  // Analytics dashboard specific tracking
  trackAnalyticsView(viewType, filters = {}) {
    this.trackEvent('analytics_viewed', {
      view_type: viewType,
      filters
    });
  }

  trackReportGeneration(reportType, parameters = {}) {
    this.trackEvent('report_generated', {
      report_type: reportType,
      parameters
    });
  }

  trackSprintAnalysis(sprintId, analysisType) {
    this.trackEvent('sprint_analysis', {
      sprint_id: sprintId,
      analysis_type: analysisType
    });
  }

  trackCapacityAnalysis(teamId, analysisType) {
    this.trackEvent('capacity_analysis', {
      team_id: teamId,
      analysis_type: analysisType
    });
  }

  // Enable/disable tracking
  enableTracking() {
    this.isTrackingEnabled = true;
  }

  disableTracking() {
    this.isTrackingEnabled = false;
  }

  // Get current session info
  getSessionInfo() {
    return {
      sessionId: this.sessionId,
      startTime: this.startTime,
      pageLoadTime: this.pageLoadTime,
      isTrackingEnabled: this.isTrackingEnabled
    };
  }
}

// Create and export a singleton instance
const analytics = new Analytics();

// Auto-track common events
document.addEventListener('DOMContentLoaded', () => {
  // Track any clicks on buttons with data-analytics attributes
  document.addEventListener('click', (event) => {
    const element = event.target.closest('[data-analytics]');
    if (element) {
      const action = element.getAttribute('data-analytics');
      const target = element.getAttribute('data-analytics-target') || element.tagName;
      const details = element.getAttribute('data-analytics-details');
      
      analytics.trackUserInteraction(action, target, details ? JSON.parse(details) : {});
    }
  });

  // Track form submissions
  document.addEventListener('submit', (event) => {
    const form = event.target;
    const formName = form.getAttribute('name') || form.getAttribute('id') || 'unknown_form';
    analytics.trackFormSubmit(formName);
  });

  // Track external link clicks
  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href]');
    if (link && link.hostname !== window.location.hostname) {
      analytics.trackEvent('external_link_click', {
        url: link.href,
        text: link.textContent.trim()
      });
    }
  });
});

export default analytics;
