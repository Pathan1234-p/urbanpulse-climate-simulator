"""Load and merge Hacknovate Pune ward + climate Excel datasets."""

from pathlib import Path

import numpy as np
import pandas as pd

from climate_simulator.data_loader import REQUIRED_COLUMNS, _add_normalized_features, _handle_missing_values

# Pune Municipal Corporation approximate population for scaling ward % shares
PMC_POPULATION_2011 = 3_124_458

WARD_NAME_ALIASES = {
    "warje-karvenagar": "Warje-Karvenagar",
    "warje-karve nagar": "Warje-Karvenagar",
    "karve rd./kothrud": "Karve Road",
    "karve road": "Karve Road",
    "ghole rd.": "Ghole Road",
    "ghole road": "Ghole Road",
    "dhole-patil rd.": "Dhole-Patil Road",
    "dhole-patil road": "Dhole-Patil Road",
    "yerwada/nagar rd.": "Nagar Road-Vadgaon Sheri",
    "nagar road-vadgaon sheri": "Nagar Road-Vadgaon Sheri",
    "dhankawadi": "Dhankawadi",
    "dhankawdi": "Dhankawadi",
    "sahakarnagar": "Sahakar Nagar",
    "sahakar nagar": "Sahakar Nagar",
    "bibvewadi": "Bibwewadi",
    "bibwewadi": "Bibwewadi",
    "bhawani peth": "Bhawani Peth",
    "tilak rd.": "Tilak Road",
    "tilak road": "Tilak Road",
    "kasba/vishrambaugwada": "Kasba-Vishrambaugwada",
    "kasba-vishrambaugwada": "Kasba-Vishrambaugwada",
    "forest area": "Forest Area under PMC",
    "forest area under pmc": "Forest Area under PMC",
    "aundh": "Aundh",
    "sangamwadi": "Sangamwadi",
    "hadapsar": "Hadapsar",
}


def _canonical_ward(name: str) -> str:
    key = str(name).strip().lower()
    return WARD_NAME_ALIASES.get(key, str(name).strip())


def _parse_ward_comparison(path: Path) -> pd.DataFrame:
    """Extract ward population % and tree % from Comparison sheet."""
    comp = pd.read_excel(path, sheet_name="Comparison", header=None)
    ward_row = comp.iloc[1, 2:]
    pop_row = comp.iloc[2, 2:]
    tree_row = comp.iloc[3, 2:]

    records = []
    for ward, pop_pct, tree_pct in zip(ward_row, pop_row, tree_row):
        if pd.isna(ward) or str(ward).strip() == "":
            continue
        name = _canonical_ward(str(ward))
        pop_pct = float(pop_pct) if pd.notna(pop_pct) else 0.0
        tree_pct = float(tree_pct) if pd.notna(tree_pct) else 0.0
        population = round((pop_pct / 100.0) * PMC_POPULATION_2011)
        records.append(
            {
                "Ward Name": name,
                "Population": population,
                "Tree Coverage": tree_pct,
            }
        )
    return pd.DataFrame(records)


def _parse_tree_counts(path: Path) -> pd.DataFrame:
    """Optional tree counts from No. of Trees sheet."""
    trees = pd.read_excel(path, sheet_name="No. of Trees", header=None)
    records = []
    for i in range(2, len(trees)):
        ward = trees.iloc[i, 2]
        count = trees.iloc[i, 3]
        if pd.isna(ward):
            continue
        records.append(
            {
                "Ward Name": _canonical_ward(str(ward)),
                "Tree Count": int(count) if pd.notna(count) else 0,
            }
        )
    return pd.DataFrame(records)


def _parse_pune_climate(path: Path) -> dict[str, float]:
    """
    Extract city-level annual rainfall (mm) and mean max temperature (C)
    from Pune synoptic Excel (station 43063).
    """
    # Primary: structured 2012 sheet with RF / Min / Max columns
    final2 = pd.read_excel(path, sheet_name="Final (2)", header=None)
    rf_cols = [1, 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34]
    max_cols = [c + 2 for c in rf_cols]

    rainfall_total = 0.0
    max_temps: list[float] = []

    for i in range(5, min(37, len(final2))):
        row = final2.iloc[i]
        for c in rf_cols:
            if c < len(row) and pd.notna(row[c]):
                try:
                    rainfall_total += float(row[c])
                except (TypeError, ValueError):
                    pass
        for c in max_cols:
            if c < len(row) and pd.notna(row[c]):
                try:
                    max_temps.append(float(row[c]))
                except (TypeError, ValueError):
                    pass

    if rainfall_total <= 0 or not max_temps:
        # Fallback: Data sheet daily records
        data = pd.read_excel(path, sheet_name="Data")
        max_temps = pd.to_numeric(data["Max"], errors="coerce").dropna().tolist()
        rainfall_total = 519.4  # documented 2012 total if daily rain missing

    return {
        "Rainfall": round(rainfall_total, 1),
        "Temperature": round(float(np.mean(max_temps)), 2),
    }


def load_pune_hacknovate_data(
    ward_excel: str | Path,
    climate_excel: str | Path,
) -> pd.DataFrame:
    """
    Merge ward population/trees with Pune city climate into simulator schema.

    Climate (rainfall, temperature) is city-wide from IMD Pune station data;
    ward-level variation comes from population and tree coverage.
    """
    ward_path = Path(ward_excel)
    climate_path = Path(climate_excel)
    if not ward_path.exists():
        raise FileNotFoundError(f"Ward dataset not found: {ward_path}")
    if not climate_path.exists():
        raise FileNotFoundError(f"Climate dataset not found: {climate_path}")

    wards = _parse_ward_comparison(ward_path)
    climate = _parse_pune_climate(climate_path)

    wards["Rainfall"] = climate["Rainfall"]
    wards["Temperature"] = climate["Temperature"]

    # Enrich with absolute tree counts where names match
    tree_df = _parse_tree_counts(ward_path)
    if not tree_df.empty:
        wards = wards.merge(tree_df, on="Ward Name", how="left")

    wards = wards[REQUIRED_COLUMNS].copy()
    wards = _handle_missing_values(wards)
    wards = _add_normalized_features(wards)
    return wards.reset_index(drop=True)


def export_merged_dataset(
    ward_excel: str | Path,
    climate_excel: str | Path,
    output_path: str | Path,
) -> Path:
    """Build merged ward file and save as Excel for the simulator."""
    df = load_pune_hacknovate_data(ward_excel, climate_excel)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    df[REQUIRED_COLUMNS].to_excel(out, index=False)
    return out
