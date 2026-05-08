import mysql.connector
from datetime import datetime
from app.config import Config
from app.utils.helpers import extract_project_user

def db_conn():
    """
    Establish and return a connection to the MySQL database 
    using configurations defined in app.config.Config.
    """
    return mysql.connector.connect(**Config.DB)

def ensure_db_schema():
    """
    Initialize the database schema if it does not already exist.
    Creates 'users' and 'scans' tables required for the dashboard.
    """
    conn = db_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username VARCHAR(255) PRIMARY KEY
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scans (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(255),
        project_name VARCHAR(255),
        total_issues INT DEFAULT 0,
        code_smells INT DEFAULT 0,
        vulnerabilities INT DEFAULT 0,
        code_coverage FLOAT DEFAULT 0,
        scan_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_project_name (project_name),
        INDEX idx_username (username)
    )""")

    conn.commit()
    cur.close()
    conn.close()

def save_data(project_key, metrics, quality, ratings, issues, analysis_date=None):
    """
    Save or update the latest SonarQube scan metrics for a specific project 
    into the local database. If a scan with the exact analysis_date already exists, it skips insertion.
    
    Args:
        project_key (str): The unique identifier of the project.
        metrics (dict): Dictionary of raw metrics fetched from SonarQube.
        quality (str): Quality gate status (e.g., 'OK', 'ERROR').
        ratings (dict): Dictionary of reliability, security, and maintainability ratings.
        issues (list): List of issues fetched from SonarQube.
        analysis_date (str): The actual analysis date from SonarQube API.
    """
    conn = db_conn()
    cur = conn.cursor()

    # Extract username using the helper function
    username, _ = extract_project_user(project_key, project_key)

    cur.execute("INSERT IGNORE INTO users (username) VALUES (%s)", (username,))

    if analysis_date:
        try:
            # Handle ISO8601 string from SonarQube (e.g., '2026-04-24T14:15:30+0530')
            clean_date = analysis_date.replace('Z', '+0000')
            # Some versions might fail fromisoformat with timezones, fallback to string slicing if needed
            scan_date = datetime.fromisoformat(clean_date).strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error parsing date {analysis_date}: {e}")
            scan_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    else:
        scan_date = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    # Check if this exact scan is already recorded
    cur.execute("SELECT id FROM scans WHERE project_name = %s AND scan_date = %s LIMIT 1", (project_key, scan_date))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False

    bugs = metrics.get("bugs", 0)
    code_smells = metrics.get("code_smells", 0)
    vulnerabilities = metrics.get("vulnerabilities", 0)
    total_issues = bugs + code_smells + vulnerabilities
    coverage = metrics.get("coverage", 0)

    cur.execute("""
    INSERT INTO scans (
        username, project_name, total_issues, code_smells, 
        vulnerabilities, code_coverage, scan_date
    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        username, project_key, total_issues, code_smells, vulnerabilities, coverage, scan_date
    ))

    conn.commit()
    cur.close()
    conn.close()
    return True

def sync_project_history(project_key):
    """
    Fetches all historical scans for a specific project from SonarQube
    and backfills them into the local database if they are missing.
    """
    try:
        from app.utils.helpers import extract_project_user
        from app.config import Config
        import requests
        from datetime import datetime

        conn = db_conn()
        cur = conn.cursor()

        username, _ = extract_project_user(project_key, project_key)
        try:
            cur.execute("INSERT IGNORE INTO users (username) VALUES (%s)", (username,))
            conn.commit()
        except Exception:
            pass
        
        # Fetch history from SonarQube API
        r = requests.get(
            f'{Config.SONAR_URL}/api/measures/search_history', 
            params={'component': project_key, 'metrics': 'bugs,vulnerabilities,code_smells,coverage'}, 
            auth=(Config.TOKEN, '')
        )
        r.raise_for_status()
        measures = r.json().get('measures', [])
        
        # Group by date
        history_by_date = {}
        for m in measures:
            metric_name = m['metric']
            for h in m.get('history', []):
                date_str = h['date']
                val = float(h.get('value', 0)) if h.get('value') else 0
                if date_str not in history_by_date:
                    history_by_date[date_str] = {'bugs': 0, 'code_smells': 0, 'vulnerabilities': 0, 'coverage': 0}
                history_by_date[date_str][metric_name] = val
                
        # Insert missing scans into DB
        for date_str, metrics in history_by_date.items():
            try:
                clean_date = date_str.replace('Z', '+0000')
                scan_date = datetime.fromisoformat(clean_date).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                continue
                
            cur.execute("SELECT id FROM scans WHERE project_name = %s AND scan_date = %s LIMIT 1", (project_key, scan_date))
            if cur.fetchone():
                continue # Already synced
                
            total_issues = metrics['bugs'] + metrics['code_smells'] + metrics['vulnerabilities']
            
            try:
                cur.execute("""
                INSERT INTO scans (
                    username, project_name, total_issues, code_smells, 
                    vulnerabilities, code_coverage, scan_date
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    username, project_key, total_issues, metrics['code_smells'], 
                    metrics['vulnerabilities'], metrics['coverage'], scan_date
                ))
                conn.commit()
            except Exception as e:
                print(f"Error inserting {scan_date}: {e}")
                conn.rollback()

        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error syncing history for {project_key}: {e}")

def fetch_issues_from_db(project_key, issue_type=None, severity=None):
    """
    Retrieve issues for a given project from the local database (if issues are cached locally).
    Supports optional filtering by issue type and severity.
    
    Args:
        project_key (str): The unique identifier of the project.
        issue_type (str, optional): The type of issue to filter by (e.g., 'BUG', 'VULNERABILITY').
        severity (str, optional): The severity level to filter by (e.g., 'BLOCKER', 'CRITICAL').
        
    Returns:
        list[dict]: A list of dictionary objects representing the matching issues.
    """
    conn = db_conn()
    cur = conn.cursor(dictionary=True)
    query = "SELECT * FROM issues WHERE project_key = %s"
    params = [project_key]

    if issue_type and issue_type.upper() != 'ALL':
        query += " AND TRIM(UPPER(`type`)) = %s"
        params.append(issue_type.upper())

    if severity:
        query += " AND TRIM(UPPER(`severity`)) = %s"
        params.append(severity.upper())

    query += " ORDER BY severity DESC"
    cur.execute(query, tuple(params))
    issues = cur.fetchall()
    cur.close()
    conn.close()
    return issues

def get_total_scans():
    """
    Returns the total number of scans executed and saved in the database.
    """
    try:
        conn = db_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(id) FROM scans")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count
    except Exception as e:
        print(f"Error fetching total scans: {e}")
        return 0
