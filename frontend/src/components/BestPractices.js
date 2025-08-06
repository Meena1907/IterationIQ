import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Button,
  Divider,
  Paper,
} from '@mui/material';
import {
  Psychology as PsychologyIcon,
  CheckCircle as CheckCircleIcon,
  Link as LinkIcon,
  People as PeopleIcon,
  AdminPanelSettings as AdminIcon,
  Assignment as ProjectManagerIcon,
  DirectionsRun as ScrumMasterIcon,
  Code as DeveloperIcon,
  BugReport as TesterIcon,
  TrendingUp as BusinessAnalystIcon,
  Star as StarIcon,
  Lightbulb as LightbulbIcon,
  OpenInNew as OpenInNewIcon,
  Book as BookIcon,
  Description as DocumentIcon,
} from '@mui/icons-material';

const BestPractices = () => {
  const [selectedRole, setSelectedRole] = useState('all');

  const roles = [
    { id: 'all', label: 'All Roles', icon: <PeopleIcon /> },
    { id: 'admin', label: 'Jira Admin', icon: <AdminIcon /> },
    { id: 'project-manager', label: 'Project Manager', icon: <ProjectManagerIcon /> },
    { id: 'scrum-master', label: 'Scrum Master', icon: <ScrumMasterIcon /> },
    { id: 'developer', label: 'Developer', icon: <DeveloperIcon /> },
    { id: 'tester', label: 'QA/Tester', icon: <TesterIcon /> },
    { id: 'business-analyst', label: 'Business Analyst', icon: <BusinessAnalystIcon /> },
  ];

  const helpData = {
    all: {
      title: "General Jira Best Practices",
      practices: [
        {
          title: "Advanced JQL Queries & Filters",
          description: "Powerful JQL queries that most teams don't know about but can save hours of manual work.",
          tips: [
            "Find issues updated in last business days: 'updated >= -5d AND updated <= -1d AND dayOfWeek(updated) not in (1,7)'",
            "Identify stale issues: 'status changed before -30d AND status not in (Done, Closed)'",
            "Find overdue issues: 'due < now() AND status not in (Done, Closed, Cancelled)'",
            "Track cross-project dependencies: 'issueFunction in linkedIssuesOf(\"project = PROJ1\")'",
            "Find issues without estimates: 'originalEstimate is EMPTY AND status not in (Done, Closed)'",
            "Identify potential scope creep: 'created >= startOfWeek() AND Sprint in openSprints()'",
            "Find issues with excessive comments: 'comment ~ \"*\" AND numberOfComments > 10'"
          ],
          resources: [
            { title: "JQL Functions Reference", url: "https://www.atlassian.com/software/jira/guides/search/jql-functions", icon: <DocumentIcon /> },
            { title: "JQL Cookbook", url: "https://www.atlassian.com/software/jira/guides/search/jql-cookbook", icon: <BookIcon /> }
          ]
        },
        {
          title: "Hidden Jira Productivity Hacks",
          description: "Lesser-known features and shortcuts that can dramatically improve your Jira efficiency.",
          tips: [
            "Use 'g + i' keyboard shortcut to quickly create issues from anywhere",
            "Bulk edit issues using JQL: Select multiple issues and use 'Tools > Bulk Change'",
            "Create issue templates using Description Templates add-on or custom fields",
            "Use issue cloning with 'More > Clone' to replicate complex issue structures",
            "Set up email handlers to create issues from emails automatically",
            "Use sub-tasks for breaking down work without losing parent context",
            "Create personal dashboards with gadgets for your specific workflow",
            "Use '@mentions' in comments to notify specific team members"
          ],
          resources: [
            { title: "Jira Keyboard Shortcuts", url: "https://www.atlassian.com/software/jira/guides/getting-started/keyboard-shortcuts", icon: <DocumentIcon /> },
            { title: "Automation Rules", url: "https://www.atlassian.com/software/jira/guides/getting-started/automation", icon: <BookIcon /> }
          ]
        },
        {
          title: "Team Performance Metrics & KPIs",
          description: "Key metrics to track team health and productivity that aren't obvious in standard reports.",
          tips: [
            "Cycle Time: Track average time from 'In Progress' to 'Done' status",
            "Lead Time: Measure from issue creation to completion",
            "Throughput: Count of issues completed per sprint/week",
            "Work Item Age: How long issues stay in each status",
            "Blocked Time: Track time issues spend in 'Blocked' status",
            "Rework Rate: Percentage of issues that return to previous states",
            "Scope Change Rate: Issues added/removed during sprints",
            "Defect Escape Rate: Bugs found in production vs. caught in testing"
          ],
          resources: [
            { title: "Agile Metrics Guide", url: "https://www.atlassian.com/agile/project-management/metrics", icon: <DocumentIcon /> },
            { title: "Control Chart Plugin", url: "https://marketplace.atlassian.com/search?query=control%20chart", icon: <BookIcon /> }
          ]
        }
      ]
    },
    admin: {
      title: "Jira Administrator Best Practices",
      practices: [
        {
          title: "System Configuration",
          description: "Properly configure Jira for optimal performance and user experience.",
          tips: [
            "Regular system maintenance and updates",
            "Configure appropriate user permissions and groups",
            "Set up custom fields and workflows strategically",
            "Monitor system performance and usage"
          ],
          resources: [
            { title: "Jira Administration Guide", url: "https://www.atlassian.com/software/jira/guides/getting-started/admin", icon: <DocumentIcon /> },
            { title: "User Management", url: "https://www.atlassian.com/software/jira/guides/getting-started/user-management", icon: <BookIcon /> }
          ]
        }
      ]
    },
    'project-manager': {
      title: "Project Manager Best Practices",
      practices: [
        {
          title: "Sprint Planning Best Practices",
          description: "Effective sprint planning techniques for better team performance.",
          tips: [
            "Set realistic sprint goals based on team velocity",
            "Break down large stories into manageable tasks",
            "Include buffer time for unexpected issues",
            "Review and adjust sprint capacity regularly"
          ],
          resources: [
            { title: "Sprint Planning Guide", url: "https://www.atlassian.com/agile/scrum/sprint-planning", icon: <DocumentIcon /> },
            { title: "Agile Project Management", url: "https://www.atlassian.com/agile/project-management", icon: <BookIcon /> }
          ]
        }
      ]
    },
    'scrum-master': {
      title: "Scrum Master Best Practices",
      practices: [
        {
          title: "Sprint Management",
          description: "Effective sprint management and team facilitation techniques.",
          tips: [
            "Facilitate daily standups effectively",
            "Remove blockers quickly and efficiently",
            "Conduct meaningful sprint retrospectives",
            "Coach team on agile principles"
          ],
          resources: [
            { title: "Scrum Guide", url: "https://scrumguides.org/scrum-guide.html", icon: <DocumentIcon /> },
            { title: "Agile Coaching", url: "https://www.atlassian.com/agile/scrum", icon: <BookIcon /> }
          ]
        }
      ]
    },
    developer: {
      title: "Developer Best Practices",
      practices: [
        {
          title: "Development Workflow",
          description: "Best practices for developers working with Jira.",
          tips: [
            "Update issue status promptly",
            "Use meaningful commit messages",
            "Link commits to Jira issues",
            "Provide clear progress updates"
          ],
          resources: [
            { title: "Development Workflow", url: "https://www.atlassian.com/software/jira/guides/getting-started/basics", icon: <DocumentIcon /> },
            { title: "Git Integration", url: "https://www.atlassian.com/software/jira/guides/getting-started/git-integration", icon: <BookIcon /> }
          ]
        }
      ]
    },
    tester: {
      title: "QA/Tester Best Practices",
      practices: [
        {
          title: "Testing Best Practices",
          description: "Effective testing practices and quality assurance techniques.",
          tips: [
            "Create comprehensive test cases",
            "Use appropriate issue types for bugs",
            "Provide detailed bug reports",
            "Track testing progress effectively"
          ],
          resources: [
            { title: "Testing Best Practices", url: "https://www.atlassian.com/software/jira/guides/getting-started/testing", icon: <DocumentIcon /> },
            { title: "Quality Assurance", url: "https://www.atlassian.com/software/jira/guides/getting-started/quality-assurance", icon: <BookIcon /> }
          ]
        }
      ]
    },
    'business-analyst': {
      title: "Business Analyst Best Practices",
      practices: [
        {
          title: "Requirements Management",
          description: "Effective requirements gathering and management techniques.",
          tips: [
            "Write clear, detailed requirements",
            "Use appropriate issue types and fields",
            "Maintain traceability between requirements",
            "Collaborate effectively with stakeholders"
          ],
          resources: [
            { title: "Requirements Management", url: "https://www.atlassian.com/software/jira/guides/getting-started/requirements", icon: <DocumentIcon /> },
            { title: "Business Analysis", url: "https://www.atlassian.com/software/jira/guides/getting-started/business-analysis", icon: <BookIcon /> }
          ]
        }
      ]
    }
  };

  const currentData = helpData[selectedRole] || helpData.all;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <PsychologyIcon sx={{ fontSize: 40, color: 'primary.main' }} />
        <Typography variant="h4" sx={{ fontWeight: 600, color: 'primary.main' }}>
          Jira Best Practices & Resources
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Left Navigation Sidebar */}
        <Grid item xs={12} md={3}>
          <Card sx={{ backgroundColor: 'primary.main', color: 'white', mb: 2 }}>
            <CardContent>
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Jira Best Practices & Resources
              </Typography>
            </CardContent>
          </Card>
          
          <Paper elevation={1}>
            <List>
              {roles.map((role) => (
                <ListItem
                  key={role.id}
                  button
                  selected={selectedRole === role.id}
                  onClick={() => setSelectedRole(role.id)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.main',
                      color: 'white',
                      '&:hover': {
                        backgroundColor: 'primary.dark',
                      },
                    },
                  }}
                >
                  <ListItemIcon sx={{ color: selectedRole === role.id ? 'white' : 'inherit' }}>
                    {role.icon}
                  </ListItemIcon>
                  <ListItemText primary={role.label} />
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>

        {/* Right Content Area */}
        <Grid item xs={12} md={9}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" gap={2} mb={3}>
                <LightbulbIcon sx={{ fontSize: 30, color: 'primary.main' }} />
                <Typography variant="h5" sx={{ fontWeight: 600, color: 'primary.main' }}>
                  {currentData.title}
                </Typography>
              </Box>

              {currentData.practices.map((practice, index) => (
                <Box key={index} sx={{ mb: 4 }}>
                  <Card sx={{ backgroundColor: 'primary.main', color: 'white', mb: 2 }}>
                    <CardContent sx={{ py: 1 }}>
                      <Box display="flex" alignItems="center" gap={1}>
                        <StarIcon sx={{ fontSize: 20 }} />
                        <Typography variant="h6" sx={{ fontWeight: 600 }}>
                          {practice.title}
                        </Typography>
                      </Box>
                    </CardContent>
                  </Card>

                  <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                    {practice.description}
                  </Typography>

                  {/* Best Practices */}
                  <Box sx={{ mb: 3 }}>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <CheckCircleIcon color="success" />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Best Practices:
                      </Typography>
                    </Box>
                    <List dense>
                      {practice.tips.map((tip, tipIndex) => (
                        <ListItem key={tipIndex} sx={{ py: 0.5 }}>
                          <ListItemText 
                            primary={tip}
                            primaryTypographyProps={{ variant: 'body2' }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Box>

                  {/* Resources & Documentation */}
                  <Box>
                    <Box display="flex" alignItems="center" gap={1} mb={1}>
                      <CheckCircleIcon color="success" />
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        Resources & Documentation:
                      </Typography>
                      <OpenInNewIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    </Box>
                    <Box display="flex" gap={1} flexWrap="wrap">
                      {practice.resources.map((resource, resourceIndex) => (
                        <Button
                          key={resourceIndex}
                          variant="outlined"
                          size="small"
                          startIcon={resource.icon}
                          href={resource.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          sx={{ textTransform: 'none' }}
                        >
                          {resource.title}
                        </Button>
                      ))}
                    </Box>
                  </Box>

                  {index < currentData.practices.length - 1 && (
                    <Divider sx={{ mt: 3 }} />
                  )}
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BestPractices; 