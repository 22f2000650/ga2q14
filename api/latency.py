from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import json
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data from the bundled JSON file
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "telemetry.json")

def load_data():
    with open(DATA_PATH, "r") as f:
        return json.load(f)

@app.post("/api/latency")
async def latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    all_data = load_data()

    result = {}
    for region in regions:
        records = [r for r in all_data if r["region"] == region]
        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": round(float(np.mean(latencies)), 4),
            "p95_latency": round(float(np.percentile(latencies, 95)), 4),
            "avg_uptime": round(float(np.mean(uptimes)), 4),
            "breaches": int(sum(1 for l in latencies if l > threshold_ms))
        }

    return JSONResponse(content=result)