# Jira Sprint Report Generator

This script generates a comprehensive sprint report for the last 2 closed sprints from a Jira board, providing insights into sprint performance and completion rates. It combines the Jira Agile API and Greenhopper API for maximum accuracy.

## Features

- Fetches the last 2 closed sprints from a specified Jira board using Agile API
- Gets detailed sprint report data using Greenhopper API
- Calculates completion rates and scope changes
- Provides insights on sprint performance
- Uses official Jira APIs for accurate data

## Prerequisites

- Python 3.x
- Required Python packages:
  - requests
  - python-dateutil

## Configuration

Update the following variables in `scripts/jira_sprint_report.py`:

```python
JIRA_URL = "https://your-domain.atlassian.net"
EMAIL = "your-email@domain.com"
API_TOKEN = "your-api-token"
BOARD_ID = "your-board-id"
```

## APIs Used

### 1. Get Latest Closed Sprints (Agile API)
```http
GET /rest/agile/1.0/board/{boardId}/sprint
```
Parameters:
- `state`: "closed"
- `maxResults`: 5
- `orderBy`: "-startDate"
- Returns: List of closed sprints sorted by start date

### 2. Get Sprint Report (Greenhopper API)
```http
GET /rest/greenhopper/1.0/rapid/charts/sprintreport
```
Parameters:
- `rapidViewId`: board_id
- `sprintId`: sprint_id
- Returns: Detailed sprint report including:
  - Completed issues
  - Not completed issues
  - Issues added during sprint
  - Sprint statistics

## Report Metrics

The script generates a report with the following metrics for each sprint:

| Metric | Description |
|--------|-------------|
| Sprint Name | Name of the sprint |
| Start Date | Sprint start date |
| End Date | Sprint end date |
| Status | Sprint status |
| Completed | Number of completed issues |
| Not Completed | Number of incomplete issues |
| Scope Change | Number of issues added during sprint |
| Completion % | Percentage of completed issues |
| Insight | Performance insights based on metrics |

## Insights Logic

The script provides insights based on the following criteria:

- **Velocity Assessment**:
  - ✅ Good velocity: Completion rate ≥ 80%
  - ⚠️ Moderate delivery: Completion rate 50-79%
  - ❌ Low delivery rate: Completion rate < 50%

- **Scope Stability**:
  - ⚠️ Unstable scope: Scope change ≥ 20% of planned scope
  - ℹ️ Minor scope changes: Scope change > 0% but < 20%

## Usage

1. Configure the script with your Jira credentials
2. Run the script:
```bash
python scripts/jira_sprint_report.py
```

## Output Example

```
Sprint Report Summary (Last 2 Closed Sprints):
Sprint Name                      Start        End          Status     Completed  Not Completed  Scope Change   Completion %  Insight
------------------------------------------------------------------------------------------------------------------------------------------------------
Vector 1May - 15 May            2024-05-01   2024-05-15   closed     12         3             4              80.0%         ✅ Good velocity | ℹ️ Minor scope changes
Vector 17 Apr - 30 Apr          2024-04-17   2024-04-30   closed     8          5             7              61.5%         ⚠️ Moderate delivery rate | ⚠️ Unstable scope
```

## Notes

- The script combines Agile API and Greenhopper API for maximum accuracy
- Agile API is used to get the list of sprints
- Greenhopper API provides detailed sprint report data that matches Jira's UI
- The report focuses on the last 2 closed sprints for better trend analysis
- Completion status and scope changes are calculated using official sprint report data 