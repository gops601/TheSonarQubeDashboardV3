import os

class Config:
    # SONAR_URL = "http://sonarqube:9000"
    SONAR_URL = os.environ.get('SONAR_URL', "http://localhost:9000")
    TOKEN = os.environ.get('SONAR_TOKEN', "squ_326c582363f61d95e4e00ce365b974f09a254a79")
    
    DB = {
        # "host": "mysql-db",
        "host": os.environ.get('DB_HOST', "localhost"),
        "user": os.environ.get('DB_USER', "root"),
        "password": os.environ.get('DB_PASSWORD', "Admin123"),
        "database": os.environ.get('DB_NAME', "sonar_dashboard")
    }

    METRIC_KEYS = ",".join([
        "bugs",
        "vulnerabilities",
        "code_smells",
        "coverage",
        "duplicated_lines_density",
        "ncloc",
        "complexity",
        "duplicated_blocks",
        "new_bugs",
        "new_vulnerabilities",
        "new_code_smells",
        "reliability_remediation_effort",
        "security_remediation_effort",
        "sqale_debt_ratio"
    ])

    RATING_MAP = {
        "1.0": "A",
        "2.0": "B",
        "3.0": "C",
        "4.0": "D",
        "5.0": "E"
    }
