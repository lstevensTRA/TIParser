"""
API configuration for client data
DO NOT modify existing configuration files
"""

# Client Profile API Configuration
CLIENT_API_CONFIG = {
    "base_url": "https://tps.logiqs.com/publicapi/2020-02-22/cases/caseinfo",
    "api_key": "4917fa0ce4694529a9b97ead1a60c932",
    "timeout": 30,
    "retry_attempts": 3
}

def get_client_api_url(case_id: str) -> str:
    """Generate complete API URL for client data"""
    return f"{CLIENT_API_CONFIG['base_url']}?apikey={CLIENT_API_CONFIG['api_key']}&CaseID={case_id}" 