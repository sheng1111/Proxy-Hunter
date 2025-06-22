import json
from unittest.mock import patch

from proxyhunter.web_app import app


def test_index_page() -> None:
    fake_results = [
        {"proxy": "1.1.1.1:8080", "status": "ok", "response_time": 0.5, "data_size": 10},
        {"proxy": "2.2.2.2:8080", "status": "failed", "response_time": None, "data_size": 0},
    ]

    with patch("proxyhunter.web_app.ProxyHunter") as MockHunter:
        instance = MockHunter.return_value
        instance.fetch_proxies.return_value = ["1.1.1.1:8080", "2.2.2.2:8080"]
        instance.check_proxies.return_value = fake_results

        client = app.test_client()
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Proxy Hunter" in body

