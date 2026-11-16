"""TerraRover simulation results API.

Exposes recorded Webots executions.
Does not start Webots or claim live simulation.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(
    prefix="/api/simulation",
    tags=["simulation"],
)

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "simulation" / "results"

JSON_DIR = RESULTS / "json"
CSV_DIR = RESULTS / "csv"
PLOT_DIR = RESULTS / "plots"

SAFE_RUN = re.compile(r"^[A-Za-z0-9_-]{1,160}$")


def validate_run_id(run_id: str):
    if not SAFE_RUN.fullmatch(run_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid simulation identifier.",
        )
    return run_id


def result_path(run_id: str):
    validate_run_id(run_id)
    return JSON_DIR / f"{run_id}_results.json"


def read_record(run_id: str):
    path = result_path(run_id)

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Simulation record not found.",
        )

    try:
        result = json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError):
        raise HTTPException(
            status_code=503,
            detail="Simulation record could not be read.",
        )

    if not isinstance(result, dict):
        raise HTTPException(
            status_code=503,
            detail="Invalid simulation record.",
        )

    # Remove absolute paths from the original computer.
    result.pop("artifacts", None)

    return result


def artifact_links(run_id: str):
    base = f"/api/simulation/runs/{run_id}/artifacts"

    csv_path = CSV_DIR / f"{run_id}_telemetry.csv"
    plot_path = PLOT_DIR / f"{run_id}_analysis.png"

    return {
        "csv": f"{base}/csv" if csv_path.is_file() else None,
        "plot": f"{base}/plot" if plot_path.is_file() else None,
    }


@router.get("/health")
def simulation_health():
    count = len(list(JSON_DIR.glob("*_results.json")))

    return {
        "service": "terrarover-simulation",
        "status": "available",
        "mode": "recorded_results",
        "webots_live": False,
        "records": count,
    }


@router.get("/runs")
def list_simulation_runs():
    runs = []

    for path in sorted(JSON_DIR.glob("*_results.json")):
        run_id = path.stem.removesuffix("_results")

        if not SAFE_RUN.fullmatch(run_id):
            continue

        runs.append({
            "run_id": run_id,
            "mode": "recorded",
            "results_url": (
                f"/api/simulation/runs/{run_id}/results"
            ),
        })

    return {
        "mode": "recorded_results",
        "live_execution": False,
        "count": len(runs),
        "runs": runs,
    }


@router.get("/runs/{run_id}/results")
def get_simulation_results(run_id: str):
    result = read_record(run_id)

    return {
        "run_id": run_id,
        "mode": "recorded",
        "is_live": False,
        "result": result,
        "artifacts": artifact_links(run_id),
    }


@router.get("/runs/{run_id}/artifacts/{kind}")
def get_simulation_artifact(run_id: str, kind: str):
    validate_run_id(run_id)

    # Require an existing simulation record.
    if not result_path(run_id).is_file():
        raise HTTPException(404, "Simulation record not found.")

    if kind == "csv":
        path = CSV_DIR / f"{run_id}_telemetry.csv"
        media_type = "text/csv"

    elif kind == "plot":
        path = PLOT_DIR / f"{run_id}_analysis.png"
        media_type = "image/png"

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported artifact type.",
        )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Simulation artifact not found.",
        )

    return FileResponse(
        path,
        media_type=media_type,
        headers={"X-Content-Type-Options": "nosniff"},
    )
