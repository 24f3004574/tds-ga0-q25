import json
from pathlib import Path
from statistics import mean

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)


DATA_PATH = Path(__file__).with_name("q-vercel-latency.json")

with open(DATA_PATH, encoding="utf-8") as f:
    telemetry = json.load(f)


class RequestBody(BaseModel):
    regions: list[str]
    threshold_ms: float


def percentile_95(values):
    values = sorted(values)

    if len(values) == 1:
        return values[0]

    position = (len(values) - 1) * 0.95
    lower = int(position)
    upper = lower + 1

    if upper >= len(values):
        return values[lower]

    fraction = position - lower
    return values[lower] + fraction * (values[upper] - values[lower])


@app.post("/")
def analytics(request: RequestBody):
    result = {}

    for region in request.regions:
        records = [
            row for row in telemetry
            if row["region"] == region
        ]

        latencies = [row["latency_ms"] for row in records]
        uptimes = [row["uptime_pct"] for row in records]

        result[region] = {
            "avg_latency": mean(latencies),
            "p95_latency": percentile_95(latencies),
            "avg_uptime": mean(uptimes),
            "breaches": sum(
                latency > request.threshold_ms
                for latency in latencies
            )
        }

    return result