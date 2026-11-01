BASE = {"email": "base@example.com", "password": "password123"}


def _auth(client):
    client.post("/auth/register", json={**BASE, "full_name": "Base"})
    token = client.post("/auth/login", json=BASE).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_register_and_me(client):
    r = client.post("/auth/register", json={"email": "reg@example.com", "password": "password123", "full_name": "Reg"})
    assert r.status_code == 201
    token = client.post("/auth/login", json={"email": "reg@example.com", "password": "password123"}).json()["access_token"]
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "reg@example.com"


def test_categories_list(client):
    h = _auth(client)
    r = client.get("/categories", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_expense_crud(client):
    h = _auth(client)
    r = client.post("/expenses", json={"amount": 10.5, "description": "lunch"}, headers=h)
    assert r.status_code == 201
    eid = r.json()["id"]
    r = client.get(f"/expenses/{eid}", headers=h)
    assert r.status_code == 200
    r = client.put(f"/expenses/{eid}", json={"amount": 12.0}, headers=h)
    assert r.status_code == 200
    assert r.json()["amount"] == 12.0
    r = client.get("/expenses", headers=h)
    assert r.status_code == 200
    r = client.delete(f"/expenses/{eid}", headers=h)
    assert r.status_code == 204


def test_budget_and_report(client):
    h = _auth(client)
    r = client.post("/budgets", json={"amount": 100.0}, headers=h)
    assert r.status_code == 201
    bid = r.json()["id"]
    r = client.get(f"/budgets/{bid}/status", headers=h)
    assert r.status_code == 200
    r = client.get("/reports/summary", headers=h)
    assert r.status_code == 200
    r = client.get("/reports/by-category", headers=h)
    assert r.status_code == 200
    r = client.get("/reports/trends", headers=h)
    assert r.status_code == 200
