from flask import Blueprint, render_template
from app.services.sonar import fetch_projects, fetch_user_email
from app.utils.helpers import extract_project_user

ui_bp = Blueprint('ui', __name__)

@ui_bp.route("/", methods=["GET"])
def dashboard():
    projects_raw = fetch_projects()

    grouped_projects = {}
    for p in projects_raw:
        original_name = p.get('name', 'Unknown')
        project_key = p.get('key', '')
        userid, proj_name = extract_project_user(original_name, project_key)
        user_email = fetch_user_email(userid)

        if userid not in grouped_projects:
            grouped_projects[userid] = []
            
        grouped_projects[userid].append({
            'key': project_key,
            'name': proj_name,
            'original_name': original_name,
            'original_key': project_key,
            'email': user_email
        })

    users_count = len(grouped_projects)
    projects_count = sum(len(projs) for projs in grouped_projects.values())
    
    from app.services.sonar import fetch_total_sonarqube_scans
    scans_count = fetch_total_sonarqube_scans(projects_raw)

    return render_template("dashboard.html", 
                           grouped_projects=grouped_projects, 
                           users_count=users_count, 
                           projects_count=projects_count, 
                           scans_count=scans_count)

@ui_bp.route("/scan_history/<project_key>", methods=["GET"])
def scan_history(project_key):
    # Fetch grouped projects for the sidebar navigation layout
    projects_raw = fetch_projects()
    grouped_projects = {}
    for p in projects_raw:
        original_name = p.get('name', 'Unknown')
        p_key = p.get('key', '')
        userid, proj_name = extract_project_user(original_name, p_key)
        user_email = fetch_user_email(userid)

        if userid not in grouped_projects:
            grouped_projects[userid] = []
            
        grouped_projects[userid].append({
            'key': p_key,
            'name': proj_name,
            'original_name': original_name,
            'original_key': p_key,
            'email': user_email
        })
    return render_template('history.html', project_key=project_key, grouped_projects=grouped_projects)
