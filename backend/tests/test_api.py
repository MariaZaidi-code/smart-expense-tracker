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


def test_income_crud(client):
    h = _auth(client)
    r = client.post("/incomes", json={"amount": 100.0, "source": "salary", "currency": "USD", "notes": "n"}, headers=h)
    assert r.status_code == 201
    iid = r.json()["id"]
    assert r.json()["notes"] == "n"
    r = client.get(f"/incomes/{iid}", headers=h)
    assert r.status_code == 200
    r = client.put(f"/incomes/{iid}", json={"amount": 120.0, "notes": "m"}, headers=h)
    assert r.status_code == 200
    assert r.json()["amount"] == 120.0
    assert r.json()["notes"] == "m"
    r = client.get("/incomes", headers=h)
    assert r.status_code == 200
    r = client.delete(f"/incomes/{iid}", headers=h)
    assert r.status_code == 204


def test_recurring_run_due(client):
    h = _auth(client)
    r = client.post("/recurring", json={"amount": 5.0, "frequency": "daily", "next_run": "2020-01-01T00:00:00"}, headers=h)
    assert r.status_code == 201
    rid = r.json()["id"]
    r = client.post("/recurring/run-due", headers=h)
    assert r.status_code == 200
    assert r.json()["created"] == 1
    r = client.get("/expenses", headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1

def test_reports_and_export_and_currency(client):
    h = _auth(client)
    client.post("/currencies", json={"code": "EUR", "rate": 2.0}, headers=h)
    client.put("/currencies/USD", json={"rate": 1.0}, headers=h)
    client.post("/expenses", json={"amount": 10.0, "currency": "EUR"}, headers=h)
    client.post("/incomes", json={"amount": 100.0}, headers=h)
    r = client.get("/reports/summary", headers=h)
    assert r.status_code == 200
    assert "savings_rate" in r.json()
    r = client.get("/reports/by-category", headers=h)
    assert r.status_code == 200
    r = client.get("/reports/trends", params={"period": "month"}, headers=h)
    assert r.status_code == 200
    r = client.get("/reports/top-expenses", params={"limit": 5}, headers=h)
    assert r.status_code == 200
    r = client.get("/reports/velocity", headers=h)
    assert r.status_code == 200
    r = client.get("/export/csv", headers=h)
    assert r.status_code == 200
    r = client.get("/export/json", headers=h)
    assert r.status_code == 200
    r = client.get("/currencies", headers=h)
    assert r.status_code == 200
