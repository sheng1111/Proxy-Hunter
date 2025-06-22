import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from proxyhunter.web_app import app, RESULTS_FILE


@pytest.fixture(autouse=True)
def cleanup_results_file():
    if os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)
    yield
    if os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)


def test_index_page():
    fake_results = [
        {"proxy": "1.1.1.1:8080", "status": "ok", "response_time": 0.5, "data_size": 10},
        {"proxy": "2.2.2.2:8080", "status": "failed", "response_time": None, "data_size": 0},
    ]
    with patch("proxyhunter.web_app.ProxyHunter") as MockHunter:
        instance = MockHunter.return_value
        instance.fetch_proxies.return_value = ["1.1.1.1:8080", "2.2.2.2:8080"]
        instance.check_proxies.return_value = fake_results
        client = app.test_client()
        # Test refresh endpoint
        resp = client.post("/refresh")
        assert resp.status_code == 200
        # Wait a bit for background thread to write results
        time.sleep(1)
        # Test data endpoint
        resp = client.get("/data")
        assert resp.status_code == 200
        data = resp.get_json()
        assert any(r["proxy"] == "1.1.1.1:8080" for r in data)
        # Test index page
        resp = client.get("/")
        assert resp.status_code == 200
        body = resp.get_data(as_text=True)
        assert "Proxy Hunter" in body
        assert "1.1.1.1:8080" in body
        assert "2.2.2.2:8080" in body

