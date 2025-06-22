"""Flask web dashboard for :class:`ProxyHunter`."""

from __future__ import annotations

import json
import threading
import os
from flask import Flask, request, render_template_string, jsonify, redirect, url_for

from .core import ProxyHunter

app = Flask(__name__)

TRANSLATIONS = {
    "en": {
        "title": "Proxy Hunter Dashboard",
        "source": "Source",
        "proxy": "Proxy",
        "status": "Status",
        "response_time": "Response Time (s)",
        "data_size": "Data Size (bytes)",
        "total": "Total",
        "success": "Success",
        "fail": "Fail",
        "average": "Average Response Time (s)",
        "language": "Language",
    },
    "zh": {
        "title": "Proxy Hunter 儀表板",
        "source": "來源",
        "proxy": "代理",
        "status": "狀態",
        "response_time": "回應時間 (秒)",
        "data_size": "資料大小 (位元組)",
        "total": "總數",
        "success": "成功",
        "fail": "失敗",
        "average": "平均回應時間 (秒)",
        "language": "語言",
    },
    "ja": {
        "title": "Proxy Hunter ダッシュボード",
        "source": "ソース",
        "proxy": "プロキシ",
        "status": "ステータス",
        "response_time": "応答時間 (秒)",
        "data_size": "データサイズ (バイト)",
        "total": "合計",
        "success": "成功",
        "fail": "失敗",
        "average": "平均応答時間 (秒)",
        "language": "言語",
    },
}

INDEX_HTML = """
<!doctype html>
<html lang="{{ lang }}">
<head>
  <meta charset="utf-8">
  <title>{{ trans.title }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css" rel="stylesheet">
  <link href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/jquery@3.7.1/dist/jquery.min.js"></script>
  <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
</head>
<body class="p-4">
  <div class="container">
    <div class="d-flex justify-content-between align-items-center mb-3">
      <h1 class="mb-0">{{ trans.title }}</h1>
      <select class="form-select w-auto" onchange="location.search='?lang='+this.value;">
        <option value="en" {% if lang=='en' %}selected{% endif %}>English</option>
        <option value="zh" {% if lang=='zh' %}selected{% endif %}>\u7e41\u9ad4\u4e2d\u6587</option>
        <option value="ja" {% if lang=='ja' %}selected{% endif %}>\u65e5\u672c\u8a9e</option>
      </select>
    </div>
    <p>{{ trans.source }}: <a href="https://free-proxy-list.net/">free-proxy-list.net</a></p>
    <p>{{ trans.total }}: {{ total }} | {{ trans.success }}: {{ success }} | {{ trans.fail }}: {{ fail }} | {{ trans.average }}: {{ average }}</p>
    <canvas id="responseChart" class="mb-4"></canvas>
    <table class="table table-striped" id="resultTable">
      <thead>
        <tr>
          <th>{{ trans.proxy }}</th>
          <th>{{ trans.status }}</th>
          <th>{{ trans.response_time }}</th>
          <th>{{ trans.data_size }}</th>
        </tr>
      </thead>
      <tbody>
      {% for item in results %}
        <tr>
          <td>{{ item.proxy }}</td>
          <td>
            {% if item.status == 'ok' %}
              <i class="bi bi-check-circle-fill text-success"></i>
            {% else %}
              <i class="bi bi-x-circle-fill text-danger"></i>
            {% endif %}
            {{ item.status }}
          </td>
          <td>{{ item.response_time if item.response_time is not none else '-' }}</td>
          <td>{{ item.data_size }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
<script>
const chartData = {{ chart_data | safe }};
const ctx = document.getElementById('responseChart').getContext('2d');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: chartData.map(d => d.proxy),
    datasets: [{
      label: '{{ trans.response_time }}',
      data: chartData.map(d => d.response_time),
      backgroundColor: 'rgba(54, 162, 235, 0.5)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1
    }]
  },
  options: {
    scales: {
      y: { beginAtZero: true }
    }
  }
});

$(document).ready(function() {
  $('#resultTable').DataTable();
});
</script>
</body>
</html>
"""

RESULTS_FILE = os.path.join(os.path.dirname(__file__), "proxy_results.jsonl")
RESULTS_LOCK = threading.Lock()

# Helper to load results from JSONL


def load_results():
    results = []
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    results.append(json.loads(line))
                except Exception:
                    continue
    return results


# Helper to append results to JSONL

def save_results(new_results):
    with RESULTS_LOCK:
        with open(RESULTS_FILE, "a", encoding="utf-8") as f:
            for r in new_results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")


# Background proxy update

def update_proxies():
    hunter = ProxyHunter()
    proxies = hunter.fetch_proxies()
    results = hunter.check_proxies(proxies)
    save_results(results)


@app.route("/refresh", methods=["POST"])
def refresh():
    threading.Thread(target=update_proxies, daemon=True).start()
    return jsonify({"status": "started"})


@app.route("/data")
def data():
    results = load_results()
    return jsonify(results)


@app.route("/")
def index() -> str:
    lang = request.args.get("lang", "en")
    trans = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    results = load_results()
    success_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = len(results) - success_count
    avg = round(
        sum(r["response_time"] for r in results if r["status"] == "ok" and r["response_time"])
        / success_count,
        2,
    ) if success_count else 0
    chart_data = json.dumps([
        {
            "proxy": r["proxy"],
            "response_time": r["response_time"] or 0,
        }
        for r in results if r["status"] == "ok"
    ])
    return render_template_string(
        INDEX_HTML + """
<script>
function refreshProxies() {
  fetch('/refresh', {method: 'POST'})
    .then(r => r.json())
    .then(_ => location.reload());
}
</script>
<button class='btn btn-primary mb-3' onclick='refreshProxies()'>Refresh Proxies</button>
""",
        results=results,
        chart_data=chart_data,
        trans=trans,
        lang=lang,
        total=len(results),
        success=success_count,
        fail=fail_count,
        average=avg,
    )


# Production WSGI entry point
# To run: gunicorn -w 4 proxyhunter.web_app:app

# Remove Flask dev server warning
if __name__ == "__main__":
    print("WARNING: For production, use a WSGI server like Gunicorn or Waitress.")
    app.run(debug=False)

