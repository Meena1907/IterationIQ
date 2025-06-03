# Jira Sprint Report Dashboard

A web-based dashboard for generating Jira sprint reports and managing labels, with CSV download support.

## Features
- **Sprint Report Web UI**: Select a Jira board and view the last 4 closed sprints with key metrics (completed, not completed, added/removed during sprint, completion %, insight, status).
- **Download as CSV**: Download the sprint report as a CSV file.
- **Label Manager**: Search, add, rename, and delete Jira labels from a modern web interface.
- **Board Selection**: Dropdown to select from all available Jira boards.

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

## Notes
- Make sure your Jira API token and credentials are correct.
- The app uses only the current status of issues at the time the sprint was closed, matching Jira's own sprint report logic.
- For any issues or feature requests, please open an issue or contact the maintainer. 