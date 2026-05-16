"""Heat risk and sustainability scoring for urban wards."""

from typing import Literal

import numpy as np
import pandas as pd

RiskCategory = Literal["LOW", "MEDIUM", "HIGH"]

HEAT_WEIGHTS = {
    "temperature": 0.4,
    "population": 0.3,
    "tree_coverage": -0.2,
    "rainfall": -0.1,
}

SUSTAINABILITY_WEIGHTS = {
    "tree_coverage": 0.45,
    "rainfall": 0.35,
    "population_pressure": 0.20,
}


def compute_heat_risk_score(
    temperature_norm: float,
    population_norm: float,
    tree_coverage_norm: float,
    rainfall_norm: float,
) -> float:
    """
    Weighted heat risk on a 0–100 scale using min-max normalized inputs.

    Higher temperature and population increase risk;
    tree coverage and rainfall reduce it.
    """
    raw = (
        temperature_norm * HEAT_WEIGHTS["temperature"]
        + population_norm * HEAT_WEIGHTS["population"]
        + tree_coverage_norm * HEAT_WEIGHTS["tree_coverage"]
        + rainfall_norm * HEAT_WEIGHTS["rainfall"]
    )
    return float(np.clip(raw * 100, 0.0, 100.0))


def categorize_risk(score: float) -> RiskCategory:
    if score < 30:
        return "LOW"
    if score <= 60:
        return "MEDIUM"
    return "HIGH"


def _population_pressure(population: float, pop_min: float, pop_max: float) -> float:
    """Normalized population pressure: 1 = highest density ward in dataset."""
    if pop_max == pop_min:
        return 0.5
    return (population - pop_min) / (pop_max - pop_min)


def compute_sustainability_score(
    tree_coverage: float,
    rainfall: float,
    population: float,
    tree_min: float,
    tree_max: float,
    rain_min: float,
    rain_max: float,
    pop_min: float,
    pop_max: float,
) -> float:
    """
    Sustainability score in [0, 1].

    Higher tree coverage and rainfall improve the score;
    higher population pressure lowers it.
    """
    def _norm(val: float, lo: float, hi: float) -> float:
        if hi == lo:
            return 0.5
        return (val - lo) / (hi - lo)

    tree_n = _norm(tree_coverage, tree_min, tree_max)
    rain_n = _norm(rainfall, rain_min, rain_max)
    pop_pressure = _population_pressure(population, pop_min, pop_max)
    green_score = 1.0 - pop_pressure

    raw = (
        tree_n * SUSTAINABILITY_WEIGHTS["tree_coverage"]
        + rain_n * SUSTAINABILITY_WEIGHTS["rainfall"]
        + green_score * SUSTAINABILITY_WEIGHTS["population_pressure"]
    )
    return float(np.clip(raw, 0.0, 1.0))


def _min_max_norm(series: pd.Series, val: float) -> float:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return 0.5
    return (val - lo) / (hi - lo)


def enrich_ward_metrics(
    df: pd.DataFrame,
    reference_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add heat risk, category, and sustainability columns to ward dataframe.

    When reference_df is provided, normalization bounds come from the baseline
    so policy scenarios produce comparable absolute score shifts.
    """
    result = df.copy()
    ref = reference_df if reference_df is not None else df
    pop_min, pop_max = ref["Population"].min(), ref["Population"].max()
    tree_min, tree_max = ref["Tree Coverage"].min(), ref["Tree Coverage"].max()
    rain_min, rain_max = ref["Rainfall"].min(), ref["Rainfall"].max()
    temp_series = ref["Temperature"]

    heat_scores = []
    categories = []
    sustainability = []

    for _, row in df.iterrows():
        heat = compute_heat_risk_score(
            _min_max_norm(temp_series, row["Temperature"]),
            _min_max_norm(ref["Population"], row["Population"]),
            _min_max_norm(ref["Tree Coverage"], row["Tree Coverage"]),
            _min_max_norm(ref["Rainfall"], row["Rainfall"]),
        )
        heat_scores.append(round(heat, 2))
        categories.append(categorize_risk(heat))
        sust = compute_sustainability_score(
            row["Tree Coverage"],
            row["Rainfall"],
            row["Population"],
            tree_min,
            tree_max,
            rain_min,
            rain_max,
            pop_min,
            pop_max,
        )
        sustainability.append(round(sust, 3))

    result["Heat Risk Score"] = heat_scores
    result["Risk Category"] = categories
    result["Sustainability Score"] = sustainability
    return result
