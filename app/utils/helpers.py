from app.config import Config

def convert_rating(value):
    return Config.RATING_MAP.get(str(value), str(value))

def issue_category(issue_type):
    if not issue_type:
        return 'UNKNOWN'
    type_upper = str(issue_type).upper()
    if type_upper == 'VULNERABILITY':
        return 'SECURITY'
    if type_upper == 'BUG':
        return 'RELIABILITY'
    if type_upper == 'CODE_SMELL':
        return 'MAINTAINABILITY'
    return 'OTHER'

def extract_project_user(original_name, project_key):
    if original_name and "-" in original_name:
        parts = original_name.rsplit("-", 1)
        if len(parts) == 2 and parts[1].strip():
            return parts[1].strip(), parts[0].strip()

    if original_name and "_" in original_name:
        parts = original_name.split("_", 1)
        if len(parts) == 2 and parts[0].strip():
            return parts[0].strip(), parts[1].strip()

    if project_key and "_" in project_key:
        parts = project_key.split("_", 1)
        if len(parts) == 2 and parts[0].strip():
            return parts[0].strip(), original_name

    return original_name, original_name
