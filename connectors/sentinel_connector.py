import requests

class SentinelConnector:
    def __init__(self, base_url: str, tenant_id: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None

    def authenticate(self):
        """
        Stub: Authenticate against Azure AD and get token for Sentinel API.
        For now, just return a mock token.
        """
        # In real implementation, call Azure AD OAuth2 endpoint
        self.token = "mock-sentinel-token"
        return self.token

    def get_rules(self):
        """
        Stub: Fetch rules from Microsoft Sentinel (Log Analytics API).
        For now, return mock rules.
        """
        return [
            {"id": "rule-101", "query": "SecurityEvent | where EventID == 4625", "source": "Sentinel"},
            {"id": "rule-102", "query": "SigninLogs | where ResultType == 50074", "source": "Sentinel"},
        ]

    def get_alert_counts(self):
        """
        Stub: Get number of alerts per rule from Sentinel.
        For now, return mock values.
        """
        return {
            "rule-101": 120,
            "rule-102": 45
        }
