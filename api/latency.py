import json
import os
import numpy as np
from http.server import BaseHTTPRequestHandler

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.json")

def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

class handler(BaseHTTPRequestHandler):

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length))

        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 180)
        all_data = load_data()

        result = {}
        for region in regions:
            records = [r for r in all_data if r["region"] == region]
            if not records:
                result[region] = {"avg_latency": None, "p95_latency": None, "avg_uptime": None, "breaches": 0}
                continue

            latencies = [r["latency_ms"] for r in records]
            uptimes = [r["uptime_pct"] for r in records]

            result[region] = {
                "avg_latency": round(float(np.mean(latencies)), 4),
                "p95_latency": round(float(np.percentile(latencies, 95)), 4),
                "avg_uptime": round(float(np.mean(uptimes)), 4),
                "breaches": int(sum(1 for l in latencies if l > threshold_ms))
            }

        response = json.dumps(result).encode()
        self.send_response(200)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)