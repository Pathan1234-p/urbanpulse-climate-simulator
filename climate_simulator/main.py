"""Urban Climate Simulation Engine — CLI entry point."""

import argparse
import sys
from pathlib import Path

import pandas as pd

from climate_simulator.data_loader import load_ward_data
from climate_simulator.recommendation_engine import format_ward_report, generate_recommendations
from climate_simulator.simulation_engine import (
    PolicyChanges,
    default_improved_policy,
    run_comparison,
    scenario_delta_summary,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DATA = DATA_DIR / "pune_wards.xlsx"
if not DEFAULT_DATA.exists():
    DEFAULT_DATA = DATA_DIR / "urban_wards.xlsx"

DISPLAY_COLS = [
    "Ward Name",
    "Heat Risk Score",
    "Risk Category",
    "Sustainability Score",
    "Recommendations",
]


def _print_section(title: str) -> None:
    width = 72
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def _print_ward_table(df: pd.DataFrame) -> None:
    for _, row in df.iterrows():
        report = format_ward_report(row)
        print(f"\n  Ward: {report['ward_name']}")
        print(f"    Heat Risk Score:      {report['heat_risk_score']}")
        print(f"    Risk Category:        {report['risk_category']}")
        print(f"    Sustainability Score: {report['sustainability_score']}")
        print("    Recommendations:")
        for rec in report["recommendations"]:
            print(f"      - {rec}")


def _print_policy(policy: PolicyChanges) -> None:
    p = policy.to_dict()
    print("\n  Policy adjustments:")
    print(f"    Tree coverage:     +{p['tree_coverage_pct']}%")
    print(f"    Rainfall:          +{p['rainfall_pct']}%")
    print(f"    Temperature:       {p['temperature_delta']:+.1f} C")
    print(f"    Population growth: +{p['population_growth_pct']}%")


def run_simulation(
    data_path: Path,
    improved_policy: PolicyChanges | None = None,
) -> None:
    print("\n  Urban Climate Simulation Engine")
    print("  Climate policy testing tool for urban planners\n")

    raw = load_ward_data(data_path)
    print(f"  Loaded {len(raw)} wards from {data_path.name}")

    improved_policy = improved_policy or default_improved_policy()
    scenarios = run_comparison(raw, improved_policy)

    for key in ("current", "improved"):
        scenario = scenarios[key]
        wards = generate_recommendations(scenario.wards)
        _print_section(scenario.name)
        if key == "improved":
            _print_policy(scenario.policy)
        _print_ward_table(wards[DISPLAY_COLS])

    _print_section("Scenario Comparison (Improved - Current)")
    delta = scenario_delta_summary(scenarios["current"], scenarios["improved"])
    print(delta.to_string())

    high_before = (
        scenarios["current"].wards["Risk Category"] == "HIGH"
    ).sum()
    high_after = (
        scenarios["improved"].wards["Risk Category"] == "HIGH"
    ).sum()
    print(f"\n  High-risk wards: {high_before} -> {high_after}")
    avg_sust_gain = delta["Sustainability Change"].mean()
    print(f"  Avg sustainability gain: {avg_sust_gain:+.3f}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Urban Climate Simulation Engine — ward-level heat risk & sustainability",
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA,
        help="Path to Excel ward dataset",
    )
    parser.add_argument(
        "--tree-pct",
        type=float,
        default=25.0,
        help="Tree coverage increase (%%) for improved scenario",
    )
    parser.add_argument(
        "--rain-pct",
        type=float,
        default=10.0,
        help="Rainfall increase (%%) for improved scenario",
    )
    parser.add_argument(
        "--temp-delta",
        type=float,
        default=-0.5,
        help="Temperature change (°C) for improved scenario",
    )
    parser.add_argument(
        "--pop-growth",
        type=float,
        default=5.0,
        help="Population growth (%%) for improved scenario",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.data.exists():
        print(f"Error: dataset not found at {args.data}", file=sys.stderr)
        print("Run: python scripts/generate_sample_data.py", file=sys.stderr)
        return 1

    policy = PolicyChanges(
        tree_coverage_pct=args.tree_pct,
        rainfall_pct=args.rain_pct,
        temperature_delta=args.temp_delta,
        population_growth_pct=args.pop_growth,
    )
    run_simulation(args.data, policy)
    return 0


if __name__ == "__main__":
    sys.exit(main())
