"""Ward-level recommendations based on heat risk and sustainability."""

from typing import Any

import pandas as pd

Recommendation = dict[str, str]

THRESHOLDS = {
    "high_heat": 60,
    "medium_heat": 30,
    "low_sustainability": 0.4,
    "low_tree_coverage": 15.0,
    "low_rainfall": 800.0,
    "high_temperature": 33.0,
    "high_population": 50000,
}


def _recommend_for_ward(row: pd.Series) -> list[str]:
    recs: list[str] = []

    heat = row["Heat Risk Score"]
    sust = row["Sustainability Score"]
    trees = row["Tree Coverage"]
    rain = row["Rainfall"]
    temp = row["Temperature"]
    pop = row["Population"]

    if trees < THRESHOLDS["low_tree_coverage"] or heat >= THRESHOLDS["medium_heat"]:
        recs.append("Increase urban trees in high-exposure zones")

    if heat >= THRESHOLDS["high_heat"] or (trees < 20 and pop > 30000):
        recs.append("Build green corridors connecting parks and transit hubs")

    if temp >= THRESHOLDS["high_temperature"] or heat >= THRESHOLDS["medium_heat"]:
        recs.append("Install cool roofs on public and commercial buildings")

    if rain < THRESHOLDS["low_rainfall"] or sust < THRESHOLDS["low_sustainability"]:
        recs.append("Improve rainwater harvesting and permeable surfaces")

    if pop >= THRESHOLDS["high_population"] and sust < 0.55:
        recs.append("Reduce population pressure via transit-oriented development")

    if heat >= THRESHOLDS["high_heat"]:
        recs.append("Deploy emergency cooling centers during heat waves")

    if not recs:
        recs.append("Maintain current green infrastructure and monitor seasonally")

    seen: set[str] = set()
    unique: list[str] = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            unique.append(r)
    return unique


def generate_recommendations(df: pd.DataFrame) -> pd.DataFrame:
    """Attach recommendation lists to each ward."""
    out = df.copy()
    out["Recommendations"] = out.apply(
        lambda row: _recommend_for_ward(row),
        axis=1,
    )
    return out


def format_ward_report(row: pd.Series) -> dict[str, Any]:
    """Structured output for a single ward."""
    recs = row.get("Recommendations", [])
    if isinstance(recs, str):
        recs = [recs]
    return {
        "ward_name": row["Ward Name"],
        "heat_risk_score": row["Heat Risk Score"],
        "risk_category": row["Risk Category"],
        "sustainability_score": row["Sustainability Score"],
        "recommendations": list(recs),
    }
