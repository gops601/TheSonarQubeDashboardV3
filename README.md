# ICTAK SonarQube Dashboard

This application is a scalable Flask-based web dashboard that integrates with SonarQube to provide graphical analysis, metrics, and issue tracking for multiple projects. It fetches live data from a SonarQube instance and stores historical scan metrics in a local MySQL database.

## 🏗️ Architecture & Project Structure

The project was recently refactored to use the **Flask Application Factory** pattern for improved scalability and maintainability.

```text
/SonarAutomationv2
├── app/
│   ├── __init__.py           # Application Factory: initializes Flask and registers blueprints
│   ├── config.py             # Configuration settings (DB credentials, Sonar URL, API Tokens)
│   ├── routes/               # Controllers
│   │   ├── api.py            # Backend API routes for fetching/saving metrics and history
│   │   └── ui.py             # Frontend UI routes (Dashboard and History pages)
│   ├── services/             # Core Business Logic
│   │   ├── database.py       # MySQL connection, schema initialization, and data persistence
│   │   └── sonar.py          # Methods interacting with the external SonarQube Web API
│   └── utils/                # Helper Functions
│       └── helpers.py        # Formatting, user extraction, and categorization utilities
├── templates/                # HTML UI Templates
│   ├── dashboard.html        # Main dashboard view with global filters and project selection
│   └── history.html          # Detailed historical scan records for specific projects
├── requirements.txt          # Python dependencies
├── run.py                    # Main entry point to run the application
└── Dockerfile                # Docker configuration (if applicable)
```

## 🚀 Features

1. **Live SonarQube Integration:** Fetches Quality Gate status, Code Smells, Vulnerabilities, Bugs, Coverage, and Duplicated Lines directly from SonarQube.
2. **Global & Project Scan History:** Tracks scan metrics over time in a local database. Includes a global filter on the dashboard to view scans across all projects within a specified date range.
3. **Issue Browser:** Categorized breakdown of issues (Blocker, Critical, Major, etc.) allowing users to drill down into specific vulnerabilities or bugs without leaving the dashboard.
4. **Automated User Categorization:** Dynamically groups projects in the sidebar based on parsed user IDs from project keys/names.

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- MySQL Server
- Access to a running SonarQube instance

### 1. Database Configuration
Ensure MySQL is running. The application requires a database (default: `sonar_dashboard`). The tables (`users` and `scans`) will be automatically created upon the first run.

You can configure database credentials by editing `app/config.py` or by setting the following environment variables:
- `DB_HOST` (default: `localhost`)
- `DB_USER` (default: `root`)
- `DB_PASSWORD` (default: `Admin123`)
- `DB_NAME` (default: `sonar_dashboard`)

### 2. SonarQube Configuration
Configure the SonarQube instance URL and Authentication Token in `app/config.py` or via environment variables:
- `SONAR_URL` (default: `http://187.127.142.34:9000`)
- `SONAR_TOKEN` (default provided in config)

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

*(Note: The main dependencies include `Flask`, `requests`, and `mysql-connector-python`)*

### 4. Run the Application
Start the Flask development server by running:
```bash
python run.py
```
The dashboard will be accessible at `http://localhost:5000`.

## 📡 API Endpoints

- `GET /` : Renders the main dashboard.
- `GET /scan_history/<project_key>` : Renders the history page for a specific project.
- `GET /api/report/<project_key>` : Fetches live SonarQube metrics, saves a snapshot to the database, and returns the JSON payload for the dashboard.
- `GET /api/metrics_history/<project_key>` : Retrieves up to 30 historical scan records for a project from the local database.
- `GET /api/all_scans?start=YYYY-MM-DD&end=YYYY-MM-DD` : Retrieves a global history of scans across all projects within a specific date range.
- `GET /api/issues/<project_key>` : Retrieves a categorized list of raw issues for a project.
