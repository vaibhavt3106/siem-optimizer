def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_rules(client):
    resp = client.get("/rules")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_autofix_rule(client, sample_rules):
    # This will fail if OpenAI API key is not set, so it should return 503
    resp = client.post("/rules/Block_Brute_Force/autofix")
    # Either 503 (no API key) or 200 (success) is acceptable for now
    assert resp.status_code in [200, 503]
    if resp.status_code == 200:
        assert "suggested_fix" in resp.json()


def test_apply_fix(client, sample_rules):
    fix = {"suggested_fix": "index=auth action=failure | stats count by user | where count > 5"}
    resp = client.post("/rules/Block_Brute_Force/apply_fix", json=fix)
    assert resp.status_code == 200
    body = resp.json()
    assert body["new_query"] == fix["suggested_fix"]


def test_history(client, sample_rules):
    resp = client.get("/rules/Block_Brute_Force/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_rollback(client, sample_rules):
    # First create some history by applying a fix
    fix = {"suggested_fix": "index=auth action=failure | stats count by user | where count > 5"}
    client.post("/rules/Block_Brute_Force/apply_fix", json=fix)
    
    # Now try to rollback
    resp = client.post("/rules/Block_Brute_Force/rollback?steps=1")
    assert resp.status_code == 200
    body = resp.json()
    assert body["rule_id"] == "Block_Brute_Force"
