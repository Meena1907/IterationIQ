# Jira Sprint Report Dashboard

A web-based dashboard for generating Jira sprint reports and managing labels, with CSV download support.

## Features
- **Sprint Report Web UI**: Select a Jira board and view the last 5 closed sprints with key metrics (initial planned, completed, not completed, added/removed during sprint, completion %, insight, status).
- **Download as CSV**: Download the sprint report as a CSV file.
- **Label Manager**: Search, add, rename, and delete Jira labels from a modern web interface.

## Setup Instructions

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd Jira_Tpm
```

### 2. Create and Activate a Virtual Environment (Recommended)
```sh
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the project root with the following:
```
JIRA_URL=https://your-jira-instance.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
```

### 5. Run the Flask App
```sh
python3 app.py
```
The app will be available at [http://localhost:5000](http://localhost:5000)

## Usage

### Web UI
- **Sprint Report**: Click "Sprint Report" in the sidebar, select a board, and click "Generate Report". View the table or download as CSV.
- **Label Manager**: Click "Label Manager" in the sidebar to search, add, rename, or delete labels.

### Command Line Script
You can also generate a sprint report from the command line:
```sh
python3 scripts/jira_sprint_report.py
```
This prints the last 4 closed sprints for the configured board in the script.

## Project Structure
```
Jira_Tpm/
├── app.py                # Main Flask app
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (not committed)
├── scripts/
│   ├── jira_sprint_report.py
│   └── __init__.py
├── templates/
│   └── index.html        # Main web UI
└── ...
```

## Sprint Report Calculation Logic

The sprint report analyzes the last 5 closed sprints for a given board and calculates various metrics. Here's how each metric is calculated:

### Data Sources
The application uses two data sources for maximum accuracy:
1. **Primary**: Jira Sprint Report API (`/rest/greenhopper/1.0/rapid/charts/sprintreport`) - Most accurate for closed sprints
2. **Fallback**: Jira Issue API (`/rest/agile/1.0/sprint/{sprint_id}/issue`) - Used when sprint report API fails

### Sprint Report Flow Diagram

```mermaid
graph TD
    A[Start Sprint Report] --> B[Fetch Board Sprints]
    B --> C[Filter Last 5 Closed Sprints]
    C --> D[For Each Sprint]
    D --> E[Call Sprint Report API]
    E --> F{API Success?}
    F -->|Yes| G[Extract Sprint Data]
    F -->|No| H[Fallback: Issue API]
    
    G --> I[Get API Fields]
    I --> J[completedIssues]
    I --> K[incompletedIssues]
    I --> L[puntedIssues]
    I --> M[issueKeysAddedDuringSprint]
    
    J --> N[Calculate Metrics]
    K --> N
    L --> N
    M --> N
    
    N --> O[Completed = len(completedIssues)]
    N --> P[Not Completed = len(incompletedIssues) + fallback logic]
    N --> Q[Added During Sprint = len(issueKeysAddedDuringSprint)]
    N --> R[Removed During Sprint = len(puntedIssues)]
    N --> S[Initial Planned = (Completed + Not Completed + Removed) - Added]
    
    O --> T[Generate Insights]
    P --> T
    Q --> T
    R --> T
    S --> T
    
    T --> U[Return Sprint Data]
    H --> V[Fallback Calculations]
    V --> U
    U --> W[Display in Table]
```

### Metric Calculations

#### 1. **Initial Planned**
- **Formula**: `(Completed + Not Completed + Removed During Sprint) - Added During Sprint`
- **Logic**: Number of issues that were in the sprint when it started (before any scope changes)
- **Purpose**: Shows the original sprint commitment and helps track scope changes

#### 2. **Completed**
- **Primary Method**: Count of issues in `completedIssues` from Jira Sprint Report API
- **Fallback Method**: Count of issues with status in `["done", "closed", "resolved"]` at current time
- **Logic**: Issues that were marked as done/completed during or by the end of the sprint

#### 3. **Not Completed**
- **Primary Method**: 
  - Uses `len(incompletedIssues)` from Sprint Report API
  - If `incompletedIssues` is empty, falls back to `len(issuesNotCompletedInCurrentSprint)`
- **Fallback Method**: Count of issues with status NOT in `["done", "closed", "resolved"]`
- **Logic**: Issues that were in the sprint at the end but not completed

#### 4. **Added During Sprint**
- **Primary Method**: Count of issues in `issueKeysAddedDuringSprint` from Sprint Report API
- **Fallback Method**: Calculated as 0 (not available via issue API)
- **Logic**: All issues that were added to the sprint after it started (both completed and not completed)

#### 5. **Removed During Sprint**
- **Primary Method**: Count of issues in `puntedIssues` from Sprint Report API
- **Fallback Method**: Calculated as 0 (not available via issue API)
- **Logic**: Issues that were removed from the sprint before it ended (scope decrease)

#### 6. **Completion Percentage**
- **Formula**: `(Completed / (Completed + Not Completed)) × 100`
- **Format**: Displayed as percentage with 1 decimal place (e.g., "75.0%")
- **Edge Case**: Shows "N/A" if total planned is 0

#### 7. **Insight**
Generated based on completion rate and scope changes:

**Completion Rate Insights:**
- **≥80%**: "✅ Good velocity"
- **<50%**: "❌ Low delivery rate"  
- **50-79%**: "⚠️ Moderate delivery rate"

**Scope Change Insights:**
- **≥20% scope change**: "⚠️ Unstable scope"
- **>0% scope change**: "ℹ️ Minor scope changes"
- **0% scope change**: No scope insight added

**Scope Change Rate Formula**: `(Added During Sprint / Initial Planned) × 100`

**Example Insights:**
- "✅ Good velocity | ℹ️ Minor scope changes"
- "❌ Low delivery rate | ⚠️ Unstable scope"
- "⚠️ Moderate delivery rate"

### API Field Mapping

| Jira Sprint Report API Field | Our Metric | Description |
|------------------------------|------------|-------------|
| `completedIssues` | Completed | Issues completed in the sprint |
| `incompletedIssues` | Not Completed | Issues not completed at sprint end |
| `puntedIssues` | Removed During Sprint | Issues removed from sprint |
| `issueKeysAddedDuringSprint` | Added During Sprint | Issues added after sprint started |

### Sprint Selection Logic

The application fetches the **5 most recent CLOSED sprints** for a board:

1. **Fetch All Sprints**: Gets all sprints from the board using pagination
2. **Filter Closed**: Only includes sprints with `state = "closed"` and valid `endDate`
3. **Sort by End Date**: Orders by `endDate` in descending order (most recent first)
4. **Take Top 5**: Selects the 5 most recently closed sprints

### Data Accuracy Notes

- **Primary Method**: Uses Jira's own Sprint Report API, which provides the most accurate data matching Jira UI
- **Fallback Method**: Uses current issue status, which may not reflect the exact state at sprint end
- **Status Mapping**: Considers `["done", "closed", "resolved"]` as completed statuses
- **Time Accuracy**: Sprint Report API provides data as it was at sprint closure time
- **Debug Logging**: Application includes debug output to help troubleshoot API response fields

## Notes
- Make sure your Jira API token and credentials are correct.
- The app prioritizes accuracy by using Jira's Sprint Report API when available.
- Fallback methods are used only when the primary API fails.
- All calculations match Jira's native sprint report logic for consistency.
- The Initial Planned metric helps track scope changes and sprint planning accuracy.
- For any issues or feature requests, please open an issue or contact the maintainer. 