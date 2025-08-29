from requests.auth import HTTPBasicAuth

class SplunkConnector:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)

    def get_rules(self):
        """Fetch saved searches (rules) from Splunk"""
        # For MVP we’ll mock this instead of hitting a real Splunk instance
        return [
            {"id": "Block_Brute_Force", "query": "index=auth action=failure | stats count by user"},
            {"id": "Rare_Process_Spawn", "query": "index=proc parent=cmd.exe | stats count by process_name"}
        ]

    def get_alert_counts(self, search_query: str, earliest="-24h", latest="now"):
        """(Stub) Return alert counts for a given query"""
        # In Sprint 1 this can return a fake value until we connect to real Splunk
        return {"count": 150}
