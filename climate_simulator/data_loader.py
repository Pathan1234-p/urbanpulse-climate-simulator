"""Load and preprocess ward-level environmental data from Excel."""

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

COLUMN_ALIASES = {
    "ward": "Ward Name",
    "ward name": "Ward Name",
    "population": "Population",
    "tree coverage": "Tree Coverage",
    "tree coverage (%)": "Tree Coverage",
    "trees": "Tree Coverage",
    "rainfall": "Rainfall",
    "temperature": "Temperature",
    "temp": "Temperature",
}

REQUIRED_COLUMNS = [
    "Ward Name",
    "Population",
    "Tree Coverage",
    "Rainfall",
    "Temperature",
]

NUMERIC_COLUMNS = ["Population", "Tree Coverage", "Rainfall", "Temperature"]


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower()
        renamed[col] = COLUMN_ALIASES.get(key, col)
    return df.rename(columns=renamed)


def load_ward_data(
    filepath: str | Path,
    sheet_name: Optional[str | int] = 0,
) -> pd.DataFrame:
    """Load Excel dataset and return preprocessed ward records."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_excel(path, sheet_name=sheet_name)
    df = _normalize_column_names(df)

    missing = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df[REQUIRED_COLUMNS].copy()
    df["Ward Name"] = df["Ward Name"].astype(str).str.strip()

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = _handle_missing_values(df)
    df = _add_normalized_features(df)
    return df.reset_index(drop=True)


def _handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Impute missing numeric values with column medians; drop wards without names."""
    df = df.dropna(subset=["Ward Name"])
    df = df[df["Ward Name"].str.len() > 0]

    for col in NUMERIC_COLUMNS:
        median_val = df[col].median()
        if pd.isna(median_val):
            median_val = 0.0
        df[col] = df[col].fillna(median_val)

    return df


def _min_max_scale(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)


def _add_normalized_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add min-max normalized columns for modeling."""
    for col in NUMERIC_COLUMNS:
        df[f"{col}_norm"] = _min_max_scale(df[col])
    return df


def extract_key_variables(df: pd.DataFrame) -> dict[str, pd.Series]:
    """Return core environmental variables as a dictionary of series."""
    return {col: df[col] for col in REQUIRED_COLUMNS}
