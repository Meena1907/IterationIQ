#!/usr/bin/env python3
import os

# Script to add Organizational Analytics to the Jira application

def add_org_analytics():
    # Read the current file
    with open('templates/index.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add Analytics navigation item between Capacity Planning and Help
    nav_search = '''                <li class="nav-item">
                    <a class="nav-link" href="#">
                        <i class="fas fa-user-clock"></i>
                        Capacity Planning
                    </a>
                </li>

                <li class="nav-item">
                    <a class="nav-link" href="#">
                        <i class="fas fa-question-circle"></i>
                        Help
                    </a>
                </li>'''
    
    nav_replace = '''                <li class="nav-item">
                    <a class="nav-link" href="#">
                        <i class="fas fa-user-clock"></i>
                        Capacity Planning
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="#">
                        <i class="fas fa-chart-line"></i>
                        Org Analytics
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" href="#">
                        <i class="fas fa-question-circle"></i>
                        Help
                    </a>
                </li>'''
    
    if nav_search in content:
        content = content.replace(nav_search, nav_replace)
        print("✅ Added Analytics navigation item")
    else:
        print("❌ Could not find navigation section to modify")
        return False
    
    # 2. Add Organizational Analytics section after Capacity Planning
    analytics_section = '''
            <!-- Organizational Analytics Content (hidden by default) -->
            <div id="orgAnalyticsSection" style="display: none;">
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="d-flex justify-content-between align-items-center">
                            <h4>�� Jira Organization Analytics</h4>
                            <div>
                                <select id="analyticsTimeRange" class="form-select d-inline-block w-auto me-2">
                                    <option value="30">Last 30 days</option>
                                    <option value="90" selected>Last 90 days</option>
                                    <option value="180">Last 6 months</option>
                                    <option value="365">Last year</option>
                                </select>
                                <button class="btn btn-outline-primary" id="refreshOrgAnalyticsBtn">
                                    <i class="fas fa-sync-alt"></i> Refresh
                                </button>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Loading Section -->
                <div id="orgAnalyticsLoading" class="text-center my-5" style="display: none;">
                    <div class="spinner-border text-primary me-2" role="status"></div>
                    <span>Loading organizational analytics...</span>
                </div>

                <!-- Error Section -->
                <div id="orgAnalyticsError" class="alert alert-danger" style="display: none;"></div>

                <!-- Summary Cards -->
                <div class="row mb-4" id="orgAnalyticsSummary">
                    <!-- Cost Overview -->
                    <div class="col-lg-3 col-md-6 mb-3">
                        <div class="card h-100 border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="text-primary mb-2">
                                    <i class="fas fa-dollar-sign fa-2x"></i>
                                </div>
                                <h3 class="text-primary mb-1" id="totalCost">$0</h3>
                                <p class="text-muted mb-0">Estimated Monthly Cost</p>
                                <small class="text-success" id="costTrend">+0% from last month</small>
                            </div>
                        </div>
                    </div>

                    <!-- Active Users -->
                    <div class="col-lg-3 col-md-6 mb-3">
                        <div class="card h-100 border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="text-success mb-2">
                                    <i class="fas fa-users fa-2x"></i>
                                </div>
                                <h3 class="text-success mb-1" id="activeUsers">0</h3>
                                <p class="text-muted mb-0">Active Users</p>
                                <small class="text-info" id="userTrend">Last 30 days</small>
                            </div>
                        </div>
                    </div>

                    <!-- Total Projects -->
                    <div class="col-lg-3 col-md-6 mb-3">
                        <div class="card h-100 border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="text-info mb-2">
                                    <i class="fas fa-project-diagram fa-2x"></i>
                                </div>
                                <h3 class="text-info mb-1" id="totalProjects">0</h3>
                                <p class="text-muted mb-0">Total Projects</p>
                                <small class="text-warning" id="projectTrend">Across all teams</small>
                            </div>
                        </div>
                    </div>

                    <!-- Total Boards -->
                    <div class="col-lg-3 col-md-6 mb-3">
                        <div class="card h-100 border-0 shadow-sm">
                            <div class="card-body text-center">
                                <div class="text-warning mb-2">
                                    <i class="fas fa-columns fa-2x"></i>
                                </div>
                                <h3 class="text-warning mb-1" id="totalBoards">0</h3>
                                <p class="text-muted mb-0">Total Boards</p>
                                <small class="text-primary" id="boardTrend">Active boards</small>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- User Activity Analysis -->
                <div class="row mb-4">
                    <div class="col-lg-8">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">User Activity Over Time</h6>
                            </div>
                            <div class="card-body">
                                <canvas id="userActivityChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-4">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">License Utilization</h6>
                            </div>
                            <div class="card-body">
                                <canvas id="licenseUtilizationChart" width="200" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Inactive Users Table -->
                <div class="row mb-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h6 class="mb-0">Inactive Users (30+ days)</h6>
                                <span class="badge bg-warning" id="inactiveUserCount">0 users</span>
                            </div>
                            <div class="card-body">
                                <div class="table-responsive">
                                    <table class="table table-sm">
                                        <thead>
                                            <tr>
                                                <th>User</th>
                                                <th>Email</th>
                                                <th>Last Login</th>
                                                <th>Days Inactive</th>
                                                <th>License Type</th>
                                                <th>Potential Savings</th>
                                            </tr>
                                        </thead>
                                        <tbody id="inactiveUsersTableBody">
                                            <tr>
                                                <td colspan="6" class="text-center text-muted">
                                                    <i class="fas fa-spinner fa-spin me-2"></i>Loading inactive users...
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Project & Board Analysis -->
                <div class="row">
                    <div class="col-lg-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Most Active Projects</h6>
                            </div>
                            <div class="card-body">
                                <canvas id="projectActivityChart" width="300" height="250"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-lg-6">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">Board Usage Distribution</h6>
                            </div>
                            <div class="card-body">
                                <canvas id="boardUsageChart" width="300" height="250"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

'''
    
    # Insert the analytics section before the Help section
    help_section_marker = '            <!-- Help Content -->'
    if help_section_marker in content:
        content = content.replace(help_section_marker, analytics_section + help_section_marker)
    else:
        # If no help section found, add before the closing main tag
        main_closing = '        </div>\n    </main>'
        content = content.replace(main_closing, analytics_section + main_closing)
    
    # 3. Add JavaScript navigation logic for Org Analytics
    nav_logic_old = '''            } else if (text === 'Help') {
                // Show help documentation
                alert('Help documentation coming soon!');'''
    
    nav_logic_new = '''            } else if (text === 'Org Analytics') {
                document.getElementById('orgAnalyticsSection').style.display = 'block';
                document.getElementById('mainTitle').textContent = 'Organization Analytics';
                loadOrgAnalytics();
            } else if (text === 'Help') {
                // Show help documentation
                alert('Help documentation coming soon!');'''
    
    content = content.replace(nav_logic_old, nav_logic_new)
    
    # 4. Add the clearSections function update
    clear_sections_old = '''            document.getElementById('capacityPlanningSection').style.display = 'none';'''
    clear_sections_new = '''            document.getElementById('capacityPlanningSection').style.display = 'none';
            document.getElementById('orgAnalyticsSection').style.display = 'none';'''
    
    content = content.replace(clear_sections_old, clear_sections_new)
    
    # 5. Add JavaScript functions for Org Analytics
    analytics_js = '''
        // Organizational Analytics functionality
        let orgAnalyticsCharts = {};

        async function loadOrgAnalytics() {
            const loadingEl = document.getElementById('orgAnalyticsLoading');
            const errorEl = document.getElementById('orgAnalyticsError');
            
            try {
                loadingEl.style.display = 'block';
                errorEl.style.display = 'none';
                
                const timeRange = document.getElementById('analyticsTimeRange').value;
                const response = await fetch(`/api/org_analytics?days=${timeRange}`);
                
                if (!response.ok) {
                    throw new Error('Failed to load organizational analytics');
                }
                
                const data = await response.json();
                updateOrgAnalyticsDashboard(data);
                
            } catch (error) {
                console.error('Error loading org analytics:', error);
                errorEl.textContent = 'Failed to load organizational analytics: ' + error.message;
                errorEl.style.display = 'block';
            } finally {
                loadingEl.style.display = 'none';
            }
        }

        function updateOrgAnalyticsDashboard(data) {
            // Update summary cards
            document.getElementById('totalCost').textContent = `$${data.cost.total.toLocaleString()}`;
            document.getElementById('costTrend').textContent = `${data.cost.trend > 0 ? '+' : ''}${data.cost.trend}% from last month`;
            document.getElementById('costTrend').className = data.cost.trend > 0 ? 'text-danger' : 'text-success';
            
            document.getElementById('activeUsers').textContent = data.users.active.toLocaleString();
            document.getElementById('userTrend').textContent = `${data.users.total} total users`;
            
            document.getElementById('totalProjects').textContent = data.projects.total.toLocaleString();
            document.getElementById('projectTrend').textContent = `${data.projects.active} active`;
            
            document.getElementById('totalBoards').textContent = data.boards.total.toLocaleString();
            document.getElementById('boardTrend').textContent = `${data.boards.active} active`;
            
            // Update inactive users count
            document.getElementById('inactiveUserCount').textContent = `${data.users.inactive.length} users`;
            
            // Render charts
            renderUserActivityChart(data.activity);
            renderLicenseChart(data.licenses);
            renderProjectActivityChart(data.projects.activity);
            renderBoardUsageChart(data.boards.usage);
            
            // Update inactive users table
            updateInactiveUsersTable(data.users.inactive);
        }

        function renderUserActivityChart(activityData) {
            const ctx = document.getElementById('userActivityChart').getContext('2d');
            
            if (orgAnalyticsCharts.userActivity) {
                orgAnalyticsCharts.userActivity.destroy();
            }
            
            orgAnalyticsCharts.userActivity = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: activityData.dates,
                    datasets: [{
                        label: 'Daily Active Users',
                        data: activityData.daily_active,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        function renderLicenseChart(licenseData) {
            const ctx = document.getElementById('licenseUtilizationChart').getContext('2d');
            
            if (orgAnalyticsCharts.license) {
                orgAnalyticsCharts.license.destroy();
            }
            
            orgAnalyticsCharts.license = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['Used', 'Available'],
                    datasets: [{
                        data: [licenseData.used, licenseData.total - licenseData.used],
                        backgroundColor: ['#36A2EB', '#E5E7EB']
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        function renderProjectActivityChart(projectData) {
            const ctx = document.getElementById('projectActivityChart').getContext('2d');
            
            if (orgAnalyticsCharts.projects) {
                orgAnalyticsCharts.projects.destroy();
            }
            
            orgAnalyticsCharts.projects = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: projectData.names,
                    datasets: [{
                        label: 'Issues Created',
                        data: projectData.issues_created,
                        backgroundColor: 'rgba(54, 162, 235, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    scales: {
                        x: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }

        function renderBoardUsageChart(boardData) {
            const ctx = document.getElementById('boardUsageChart').getContext('2d');
            
            if (orgAnalyticsCharts.boards) {
                orgAnalyticsCharts.boards.destroy();
            }
            
            orgAnalyticsCharts.boards = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: boardData.names,
                    datasets: [{
                        data: boardData.usage,
                        backgroundColor: [
                            '#FF6384',
                            '#36A2EB',
                            '#FFCE56',
                            '#4BC0C0',
                            '#9966FF',
                            '#FF9F40'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        function updateInactiveUsersTable(inactiveUsers) {
            const tbody = document.getElementById('inactiveUsersTableBody');
            
            if (inactiveUsers.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center text-success">
                            <i class="fas fa-check-circle me-2"></i>No inactive users found!
                        </td>
                    </tr>
                `;
                return;
            }
            
            tbody.innerHTML = inactiveUsers.map(user => `
                <tr>
                    <td>${user.displayName}</td>
                    <td>${user.emailAddress}</td>
                    <td>${new Date(user.lastLogin).toLocaleDateString()}</td>
                    <td>
                        <span class="badge bg-warning">${user.daysInactive} days</span>
                    </td>
                    <td>${user.licenseType}</td>
                    <td class="text-success">$${user.potentialSavings}/month</td>
                </tr>
            `).join('');
        }

        // Event listeners for Org Analytics
        document.getElementById('analyticsTimeRange').addEventListener('change', loadOrgAnalytics);
        document.getElementById('refreshOrgAnalyticsBtn').addEventListener('click', loadOrgAnalytics);

'''
    
    # Add the JavaScript before the closing script tag
    script_closing = '        </script>'
    content = content.replace(script_closing, analytics_js + script_closing)
    
    # Write the updated content
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Successfully added Organizational Analytics!")
    print("Features added:")
    print("- Navigation item: 'Org Analytics'")
    print("- Cost tracking and trends")
    print("- Active/inactive user analysis")
    print("- Project and board statistics") 
    print("- License utilization monitoring")
    print("- Inactive users identification")
    print("- Visual charts and dashboards")

    return True

if __name__ == "__main__":
    if add_org_analytics():
        print("✅ Successfully added Organizational Analytics navigation!")
    else:
        print("❌ Failed to add Organizational Analytics")
