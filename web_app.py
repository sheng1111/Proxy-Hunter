import re
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, render_template_string

app = Flask(__name__)

INDEX_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\">
  <title>Proxy Hunter Dashboard</title>
  <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"p-4\">
  <div class=\"container\">
    <h1 class=\"mb-4\">Proxy Hunter Dashboard</h1>
    <p>Source: <a href=\"https://free-proxy-list.net/\">free-proxy-list.net</a></p>
    <table class=\"table table-striped\">
      <thead>
        <tr><th>Proxy</th><th>Status</th><th>Response Time (s)</th><th>Data Size (bytes)</th></tr>
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
</body>
</html>
"""

def fetch_proxies():
    resp = requests.get('https://free-proxy-list.net/')
    resp.raise_for_status()
    ips = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+', resp.text)
    return list(dict.fromkeys(ips))

def check_proxy(ip):
    start = time.time()
    try:
        resp = requests.get(
            'https://api.ipify.org?format=json',
            proxies={'http': ip, 'https': ip},
            timeout=5
        )
        resp.raise_for_status()
        elapsed = time.time() - start
        size = len(resp.content)
        return {'proxy': ip, 'status': 'ok', 'response_time': round(elapsed, 2), 'data_size': size}
    except requests.RequestException:
        return {'proxy': ip, 'status': 'failed', 'response_time': None, 'data_size': 0}

@app.route('/')
def index():
    proxies = fetch_proxies()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_proxy, proxies))
    return render_template_string(INDEX_HTML, results=results)

if __name__ == '__main__':
    app.run(debug=True)