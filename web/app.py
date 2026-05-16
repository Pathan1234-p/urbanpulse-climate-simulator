"""Urban Climate Simulation Engine — web dashboard."""

import sys
import webbrowser
from pathlib import Path
from threading import Timer

from flask import Flask, jsonify, render_template, request

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from climate_simulator.data_loader import load_ward_data
from climate_simulator.recommendation_engine import format_ward_report, generate_recommendations
from climate_simulator.simulation_engine import (
    PolicyChanges,
    run_comparison,
    scenario_delta_summary,
)

DATA_DIR = ROOT / "data"
DEFAULT_DATA = DATA_DIR / "pune_wards.xlsx"
if not DEFAULT_DATA.exists():
    DEFAULT_DATA = DATA_DIR / "urban_wards.xlsx"

app = Flask(
    __name__,
    template_folder=str(Path(__file__).parent / "templates"),
    static_folder=str(Path(__file__).parent / "static"),
)

_baseline_cache: dict | None = None


def _get_baseline():
    global _baseline_cache
    if _baseline_cache is None:
        df = load_ward_data(DEFAULT_DATA)
        _baseline_cache = {"raw": df}
    return _baseline_cache["raw"]


def _wards_payload(df) -> list[dict]:
    enriched = generate_recommendations(df)
    return [format_ward_report(row) for _, row in enriched.iterrows()]


def _summary(df) -> dict:
    high = int((df["Risk Category"] == "HIGH").sum())
    medium = int((df["Risk Category"] == "MEDIUM").sum())
    low = int((df["Risk Category"] == "LOW").sum())
    return {
        "ward_count": len(df),
        "high_risk": high,
        "medium_risk": medium,
        "low_risk": low,
        "avg_heat_risk": round(float(df["Heat Risk Score"].mean()), 2),
        "avg_sustainability": round(float(df["Sustainability Score"].mean()), 3),
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/simulate", methods=["POST"])
def simulate():
    body = request.get_json(silent=True) or {}
    policy = PolicyChanges(
        tree_coverage_pct=float(body.get("tree_pct", 25)),
        rainfall_pct=float(body.get("rain_pct", 10)),
        temperature_delta=float(body.get("temp_delta", -0.5)),
        population_growth_pct=float(body.get("pop_growth", 5)),
    )

    baseline = _get_baseline()
    scenarios = run_comparison(baseline, policy)
    delta_df = scenario_delta_summary(scenarios["current"], scenarios["improved"])

    delta_records = []
    for ward, row in delta_df.iterrows():
        delta_records.append(
            {
                "ward_name": ward,
                "heat_risk_change": float(row["Heat Risk Change"]),
                "sustainability_change": float(row["Sustainability Change"]),
                "risk_before": row["Risk Category (Before)"],
                "risk_after": row["Risk Category (After)"],
            }
        )

    return jsonify(
        {
            "current": {
                "name": scenarios["current"].name,
                "wards": _wards_payload(scenarios["current"].wards),
                "summary": _summary(scenarios["current"].wards),
            },
            "improved": {
                "name": scenarios["improved"].name,
                "wards": _wards_payload(scenarios["improved"].wards),
                "summary": _summary(scenarios["improved"].wards),
                "policy": policy.to_dict(),
            },
            "comparison": delta_records,
        }
    )


@app.route("/api/wards/raw")
def raw_wards():
    df = _get_baseline()
    cols = ["Ward Name", "Population", "Tree Coverage", "Rainfall", "Temperature"]
    return jsonify(df[cols].to_dict(orient="records"))


def open_browser(url: str) -> None:
    webbrowser.open(url)


if __name__ == "__main__":
    url = "http://127.0.0.1:5000"
    Timer(1.2, open_browser, args=[url]).start()
    print("\n  UrbanPulse Climate Simulator")
    print(f"  Open in browser: {url}\n")
    app.run(host="127.0.0.1", port=5000, debug=False)
