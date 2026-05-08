from flask import Blueprint, jsonify, request, redirect, url_for
from datetime import datetime
from app.services.sonar import fetch_metrics, fetch_quality, fetch_ratings, fetch_issues
from app.services.database import save_data, db_conn

api_bp = Blueprint('api', __name__)

@api_bp.route("/api/report/<project_key>", methods=["GET"])
def api_report(project_key):
    try:
        # Fetch latest data from SonarQube directly
        print(f"Fetching data for project: {project_key}")
        metrics = fetch_metrics(project_key)
        print(f"Metrics fetched: {len(metrics)} items")

        quality = fetch_quality(project_key)
        print(f"Quality status: {quality}")

        ratings = fetch_ratings(project_key)
        print(f"Ratings fetched: {len(ratings)} items")

        issues = fetch_issues(project_key)
        print(f"Issues fetched: {len(issues)} items")

        # Fetch last analysis date
        from app.services.sonar import fetch_last_analysis_date
        analysis_date = fetch_last_analysis_date(project_key)

        # Save to database in the background (or rather, synchronously before returning)
        try:
            inserted = save_data(project_key, metrics, quality, ratings, issues, analysis_date)
            if inserted:
                print(f"New scan analysis detected and saved to DB: {analysis_date}")
            else:
                print(f"Scan already exists in DB for analysis date: {analysis_date}. Skipped inserting duplicate.")
        except Exception as e:
            print(f"Failed to save data to DB: {e}")

        return jsonify({
            "metrics": metrics,
            "quality": {
                "status": quality,
                "checked_at": datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            },
            "ratings": ratings,
            "issues": issues,
            "project_key": project_key
        })
    except Exception as e:
        print(f"Error in api_report: {e}")
        return jsonify({"error": str(e)}), 500

@api_bp.route("/api/metrics_history/<project_key>", methods=["GET"])
def api_metrics_history(project_key):
    try:
        from app.services.database import sync_project_history
        sync_project_history(project_key)

        conn = db_conn()
        cur = conn.cursor(dictionary=True)
        cur.execute(
            "SELECT scan_date, total_issues, code_smells, vulnerabilities, code_coverage "
            "FROM scans WHERE project_name = %s ORDER BY scan_date DESC LIMIT 500",
            (project_key,)
        )
        history = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/api/all_scans", methods=["GET"])
def api_all_scans():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    try:
        conn = db_conn()
        cur = conn.cursor(dictionary=True)
        query = "SELECT scan_date, project_name, total_issues, code_smells, vulnerabilities, code_coverage FROM scans WHERE 1=1"
        params = []
        if start_date:
            query += " AND DATE(scan_date) >= %s"
            params.append(start_date)
        if end_date:
            query += " AND DATE(scan_date) <= %s"
            params.append(end_date)
        query += " ORDER BY scan_date DESC LIMIT 100"
        
        cur.execute(query, tuple(params))
        scans = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"scans": scans})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/fetch/<project_key>", methods=["GET"])
def fetch_project(project_key):
    metrics = fetch_metrics(project_key)
    quality = fetch_quality(project_key)
    ratings = fetch_ratings(project_key)
    issues = fetch_issues(project_key)

    try:
        save_data(project_key, metrics, quality, ratings, issues)
    except Exception as e:
        print(f"Failed to save data to DB: {e}")

    return redirect(url_for('ui.dashboard'))

@api_bp.route("/api/issues/<project_key>", methods=["GET"])
def api_issues(project_key):
    issue_type = request.args.get('type')
    severity = request.args.get('severity')
    try:
        # Fetch live from SonarQube since the local issues table was removed
        all_issues = fetch_issues(project_key)
        if issue_type and issue_type.upper() != 'ALL':
            issue_type_value = issue_type.upper()
            all_issues = [issue for issue in all_issues if str(issue.get('type', '')).upper() == issue_type_value]
        if severity:
            severity_value = severity.upper()
            all_issues = [issue for issue in all_issues if str(issue.get('severity', '')).upper() == severity_value]
        return jsonify({"issues": all_issues})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route("/api/issue_source/<project_key>", methods=["GET"])
def api_issue_source(project_key):
    component = request.args.get('component')
    line = request.args.get('line', type=int)
    if not component or not line:
        return jsonify({"error": "Missing component or line"}), 400

    try:
        from app.config import Config
        import requests
        
        start_line = max(1, line - 5)
        end_line = line + 5
        
        r = requests.get(
            f"{Config.SONAR_URL}/api/sources/lines",
            params={'key': component, 'from': start_line, 'to': end_line},
            auth=(Config.TOKEN, '')
        )
        r.raise_for_status()
        return jsonify(r.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500
