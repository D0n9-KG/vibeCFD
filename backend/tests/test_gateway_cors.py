import importlib
from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.channels.service as channel_service


def test_gateway_allows_local_frontend_dev_origin(monkeypatch) -> None:
    gateway_app = importlib.import_module("app.gateway.app")

    class _DummyChannelService:
        def get_status(self) -> dict:
            return {"service_running": False, "channels": {}}

    async def fake_start_channel_service() -> _DummyChannelService:
        return _DummyChannelService()

    async def fake_stop_channel_service() -> None:
        return None

    monkeypatch.setattr(gateway_app, "get_app_config", lambda: object())
    monkeypatch.setattr(
        gateway_app,
        "get_gateway_config",
        lambda: SimpleNamespace(host="0.0.0.0", port=8001),
    )
    monkeypatch.setattr(
        channel_service,
        "start_channel_service",
        fake_start_channel_service,
    )
    monkeypatch.setattr(
        channel_service,
        "stop_channel_service",
        fake_stop_channel_service,
    )

    app = gateway_app.create_app()

    with TestClient(app) as client:
        response = client.options(
            "/api/models",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
