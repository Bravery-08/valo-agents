from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_health():
    res = client.get("/healthz")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"


def test_maps_mocked(monkeypatch):
    from app.services.valo_service import ValoService

    def fake_get_map_pool(self):
        return ["Ascent", "Bind"]

    monkeypatch.setattr(ValoService, "get_map_pool", fake_get_map_pool)
    res = client.get("/maps")
    assert res.status_code == 200
    assert res.json() == {"maps": ["Ascent", "Bind"]}


def test_agents_mocked(monkeypatch):
    from app.services.valo_service import ValoService

    def fake_get_agents_for_map(self, m):
        return {"Map": m, 1: "Jett", 2: "Sova"}

    monkeypatch.setattr(ValoService, "get_agents_for_map", fake_get_agents_for_map)
    res = client.get("/agents/Ascent")
    assert res.status_code == 200
    assert res.json() == {"map": "Ascent", "agents": {"1": "Jett", "2": "Sova"}}
