"""Build merged Pune ward dataset from Hacknovate source files."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from climate_simulator.pune_data_loader import export_merged_dataset

WARD_FILE = Path(
    r"C:\Users\anasp\Downloads\Hacknovate\D4 PS-1-Ward-wise Comparison of Population and No. of Trees (In %)02dac97.xlsx"
)
CLIMATE_FILE = Path(
    r"C:\Users\anasp\Downloads\Hacknovate\D4 PS-1-Pune rainfall and temperature dataf1939c3.xlsx"
)
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "pune_wards.xlsx"


def main() -> None:
    import pandas as pd

    out = export_merged_dataset(WARD_FILE, CLIMATE_FILE, OUTPUT)
    df = pd.read_excel(out)
    print(f"Saved {len(df)} Pune wards to {out}")
    print(df[["Ward Name", "Population", "Tree Coverage", "Rainfall", "Temperature"]].to_string(index=False))


if __name__ == "__main__":
    main()
