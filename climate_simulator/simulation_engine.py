"""Policy scenario simulation for urban climate planning."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from climate_simulator.risk_calculator import enrich_ward_metrics


@dataclass
class PolicyChanges:
    """Relative or absolute adjustments applied to all wards."""

    tree_coverage_pct: float = 0.0
    rainfall_pct: float = 0.0
    temperature_delta: float = 0.0
    population_growth_pct: float = 0.0

    def to_dict(self) -> dict[str, float]:
        return {
            "tree_coverage_pct": self.tree_coverage_pct,
            "rainfall_pct": self.rainfall_pct,
            "temperature_delta": self.temperature_delta,
            "population_growth_pct": self.population_growth_pct,
        }


@dataclass
class ScenarioResult:
    name: str
    wards: pd.DataFrame
    policy: PolicyChanges = field(default_factory=PolicyChanges)


def apply_policy_changes(
    df: pd.DataFrame,
    policy: PolicyChanges,
) -> pd.DataFrame:
    """Apply policy deltas and return a modified copy of ward data."""
    modified = df[
        ["Ward Name", "Population", "Tree Coverage", "Rainfall", "Temperature"]
    ].copy()

    if policy.tree_coverage_pct != 0:
        modified["Tree Coverage"] = modified["Tree Coverage"] * (
            1 + policy.tree_coverage_pct / 100
        )

    if policy.rainfall_pct != 0:
        modified["Rainfall"] = modified["Rainfall"] * (1 + policy.rainfall_pct / 100)

    if policy.temperature_delta != 0:
        modified["Temperature"] = modified["Temperature"] + policy.temperature_delta

    if policy.population_growth_pct != 0:
        modified["Population"] = modified["Population"] * (
            1 + policy.population_growth_pct / 100
        )

    modified["Tree Coverage"] = modified["Tree Coverage"].clip(lower=0)
    modified["Rainfall"] = modified["Rainfall"].clip(lower=0)
    modified["Population"] = modified["Population"].clip(lower=0)

    return modified


def run_scenario(
    baseline_df: pd.DataFrame,
    name: str,
    policy: PolicyChanges | None = None,
    reference_df: pd.DataFrame | None = None,
) -> ScenarioResult:
    """Run a single scenario: apply policy, recompute metrics."""
    policy = policy or PolicyChanges()
    ref = reference_df if reference_df is not None else baseline_df
    adjusted = apply_policy_changes(baseline_df, policy)
    enriched = enrich_ward_metrics(adjusted, reference_df=ref)
    return ScenarioResult(name=name, wards=enriched, policy=policy)


def run_comparison(
    baseline_df: pd.DataFrame,
    improved_policy: PolicyChanges,
) -> dict[str, ScenarioResult]:
    """Run current vs improved environmental scenario."""
    current = run_scenario(baseline_df, "Current Scenario")
    improved = run_scenario(
        baseline_df,
        "Improved Environmental Scenario",
        improved_policy,
        reference_df=baseline_df,
    )
    return {"current": current, "improved": improved}


def scenario_delta_summary(
    current: ScenarioResult,
    improved: ScenarioResult,
) -> pd.DataFrame:
    """Per-ward change in heat risk and sustainability between scenarios."""
    cur = current.wards.set_index("Ward Name")
    imp = improved.wards.set_index("Ward Name")

    delta = pd.DataFrame(
        {
            "Heat Risk Change": imp["Heat Risk Score"] - cur["Heat Risk Score"],
            "Sustainability Change": imp["Sustainability Score"]
            - cur["Sustainability Score"],
            "Risk Category (Before)": cur["Risk Category"],
            "Risk Category (After)": imp["Risk Category"],
        }
    )
    return delta.round(3)


def default_improved_policy() -> PolicyChanges:
    """Standard green-infrastructure improvement scenario."""
    return PolicyChanges(
        tree_coverage_pct=25.0,
        rainfall_pct=10.0,
        temperature_delta=-0.5,
        population_growth_pct=5.0,
    )
