"""Flask web dashboard for :class:`ProxyHunter`."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, render_template_string

from proxy_hunter import ProxyHunter


app = Flask(__name__)


INDEX_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Proxy Hunter Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
</head>
<body class="p-4">
  <div class="container">
    <h1 class="mb-4">Proxy Hunter Dashboard</h1>
    <p>Source: <a href="https://free-proxy-list.net/">free-proxy-list.net</a></p>
    <canvas id="responseChart" class="mb-4"></canvas>
    <table class="table table-striped">
      <thead>
        <tr>
          <th>Proxy</th>
          <th>Status</th>
          <th>Response Time (s)</th>
          <th>Data Size (bytes)</th>
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
      label: 'Response Time (s)',
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
    hunter = ProxyHunter()
    proxies = hunter.fetch_proxies()
    results = hunter.check_proxies(proxies)
    chart_data = json.dumps([
        {
            "proxy": r["proxy"],
            "response_time": r["response_time"] or 0,
        }
        for r in results
    ])
    return render_template_string(INDEX_HTML, results=results, chart_data=chart_data)


if __name__ == "__main__":
    app.run(debug=True)
