import requests
from app.config import Config
from app.utils.helpers import convert_rating

def fetch_projects():
    try:
        r = requests.get(f"{Config.SONAR_URL}/api/projects/search", auth=(Config.TOKEN, ""))
        r.raise_for_status()
        return r.json().get("components", [])
    except Exception as e:
        print(f"Error fetching projects from {Config.SONAR_URL}: {e}")
        try:
            return r.json().get("components", [])
        except:
            return []

def fetch_user_email(login):
    try:
        r = requests.get(
            f"{Config.SONAR_URL}/api/users/search",
            params={"q": login, "ps": 1},
            auth=(Config.TOKEN, "")
        )
        users = r.json().get("users", [])
        if users:
            return users[0].get("email", login) or login
        return login
    except:
        return login

def fetch_metrics(project_key):
    try:
        print(f"Fetching metrics for project: {project_key}")
        params = {
            "component": project_key,
            "metricKeys": Config.METRIC_KEYS
        }
        r = requests.get(f"{Config.SONAR_URL}/api/measures/component", params=params, auth=(Config.TOKEN, ""))
        r.raise_for_status()

        data = r.json()
        metrics = {}

        for m in data.get("component", {}).get("measures", []):
            key = m["metric"]
            value = m.get("value", 0)
            try:
                metrics[key] = float(value)
            except (TypeError, ValueError):
                metrics[key] = value

        print(f"Successfully fetched {len(metrics)} metrics")
        return metrics
    except requests.exceptions.RequestException as e:
        print(f"Request error fetching metrics: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error fetching metrics: {e}")
        return {}

def fetch_quality(project_key):
    try:
        print(f"Fetching quality status for project: {project_key}")
        r = requests.get(
            f"{Config.SONAR_URL}/api/qualitygates/project_status",
            params={"projectKey": project_key},
            auth=(Config.TOKEN, "")
        )
        r.raise_for_status()
        status = r.json().get("projectStatus", {}).get("status", "UNKNOWN")
        print(f"Quality status: {status}")
        return status
    except requests.exceptions.RequestException as e:
        print(f"Request error fetching quality: {e}")
        return "UNKNOWN"
    except Exception as e:
        print(f"Unexpected error fetching quality: {e}")
        return "UNKNOWN"

def fetch_ratings(project_key):
    try:
        print(f"Fetching ratings for project: {project_key}")
        params = {
            "component": project_key,
            "metricKeys": "reliability_rating,security_rating,sqale_rating"
        }
        r = requests.get(f"{Config.SONAR_URL}/api/measures/component", params=params, auth=(Config.TOKEN, ""))
        r.raise_for_status()

        data = r.json()
        ratings = {}

        for m in data.get("component", {}).get("measures", []):
            key = m["metric"]
            value = m.get("value", "")
            base = key.replace("_rating", "") if key.endswith("_rating") else key
            ratings[base] = convert_rating(value)
            try:
                ratings[f"{base}_score"] = float(value)
            except (TypeError, ValueError):
                ratings[f"{base}_score"] = None

        print(f"Successfully fetched {len(ratings)} ratings")
        return ratings
    except requests.exceptions.RequestException as e:
        print(f"Request error fetching ratings: {e}")
        return {}
    except Exception as e:
        print(f"Unexpected error fetching ratings: {e}")
        return {}

def fetch_issues(project_key):
    all_issues = []
    page = 1
    page_size = 500

    print(f"Fetching issues for project: {project_key}")

    while True:
        try:
            r = requests.get(
                f"{Config.SONAR_URL}/api/issues/search",
                params={"componentKeys": project_key, "ps": page_size, "p": page},
                auth=(Config.TOKEN, "")
            )
            r.raise_for_status()
            data = r.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)

            total = data.get("total", 0)
            print(f"Fetched page {page}: {len(issues)} issues (total so far: {len(all_issues)}/{total})")

            if len(all_issues) >= total or len(issues) < page_size:
                break

            page += 1
        except requests.exceptions.RequestException as e:
            print(f"Request error fetching issues page {page}: {e}")
            break
        except Exception as e:
            print(f"Unexpected error fetching issues page {page}: {e}")
            break

    print(f"Successfully fetched {len(all_issues)} total issues")
    return all_issues

def fetch_last_analysis_date(project_key):
    try:
        r = requests.get(
            f"{Config.SONAR_URL}/api/project_analyses/search",
            params={"project": project_key, "ps": 1},
            auth=(Config.TOKEN, "")
        )
        r.raise_for_status()
        analyses = r.json().get("analyses", [])
        if analyses:
            return analyses[0].get("date")
        return None
    except Exception as e:
        print(f"Error fetching last analysis date: {e}")
        return None

def fetch_total_sonarqube_scans(projects):
    """
    Given a list of project dictionaries (from fetch_projects),
    queries the total number of analyses for each and returns the sum.
    """
    total = 0
    for p in projects:
        try:
            project_key = p.get("key")
            if not project_key: continue
            
            r = requests.get(
                f"{Config.SONAR_URL}/api/project_analyses/search",
                params={"project": project_key, "ps": 1},
                auth=(Config.TOKEN, "")
            )
            r.raise_for_status()
            total += r.json().get("paging", {}).get("total", 0)
        except Exception as e:
            print(f"Error fetching analyses count for {project_key}: {e}")
    return total
