BASE = {"email": "ai@example.com", "password": "password123"}


def _auth(client):
    client.post("/auth/register", json={**BASE, "full_name": "AI"})
    token = client.post("/auth/login", json=BASE).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_ai_categorize(client):
    h = _auth(client)
    r = client.post("/ai/categorize", json={"description": "lunch", "amount": 10.0}, headers=h)
    assert r.status_code == 200
    assert r.json()["category"] == "Food"


def test_ai_insights(client):
    h = _auth(client)
    client.post("/expenses", json={"amount": 10.0, "description": "lunch"}, headers=h)
    r = client.post("/ai/insights", headers=h)
    assert r.status_code == 200
    assert "insights" in r.json()


def test_ai_anomalies(client):
    h = _auth(client)
    client.post("/expenses", json={"amount": 10.0, "description": "lunch"}, headers=h)
    r = client.post("/ai/anomalies", headers=h)
    assert r.status_code == 200
    assert "anomalies" in r.json()


def test_ai_query(client):
    h = _auth(client)
    client.post("/expenses", json={"amount": 10.0, "description": "lunch"}, headers=h)
    r = client.post("/ai/query", json={"question": "total spent"}, headers=h)
    assert r.status_code == 200
    assert "answer" in r.json()


def test_auto_categorize(client):
    h = _auth(client)
    r = client.post("/expenses", json={"amount": 10.0, "description": "uber ride"}, headers=h)
    assert r.status_code == 201
    assert r.json()["category_id"] is not None
