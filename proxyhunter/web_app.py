"""Flask web dashboard for :class:`ProxyHunter`."""

from __future__ import annotations

import json
from flask import Flask, request, render_template_string

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
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
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
    <table class="table table-striped">
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
          <td>{{ item.status }}</td>
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
</script>
</body>
</html>
"""


@app.route("/")
def index() -> str:
    lang = request.args.get("lang", "en")
    trans = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    hunter = ProxyHunter()
    proxies = hunter.fetch_proxies()
    results = hunter.check_proxies(proxies)
    success_count = sum(1 for r in results if r["status"] == "ok")
    fail_count = len(results) - success_count
    avg = round(
        sum(r["response_time"] for r in results if r["response_time"])
        / success_count,
        2,
    ) if success_count else 0
    chart_data = json.dumps([
        {
            "proxy": r["proxy"],
            "response_time": r["response_time"] or 0,
        }
        for r in results
    ])
    return render_template_string(
        INDEX_HTML,
        results=results,
        chart_data=chart_data,
        trans=trans,
        lang=lang,
        total=len(results),
        success=success_count,
        fail=fail_count,
        average=avg,
    )


if __name__ == "__main__":
    app.run(debug=False)

