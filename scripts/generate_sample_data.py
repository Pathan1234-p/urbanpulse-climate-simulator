"""Generate sample ward-level environmental dataset for UrbanPulse."""

from pathlib import Path

import pandas as pd

DATA = [
    ("Central Ward", 45000, 12.5, 850, 34.2),
    ("Riverside", 28000, 28.0, 1200, 31.5),
    ("Industrial East", 62000, 5.0, 620, 36.8),
    ("Green Heights", 18000, 45.0, 1100, 29.1),
    ("Market District", 55000, 8.0, 780, 35.4),
    ("University Quarter", 32000, 22.0, 950, 32.0),
    ("Harbor South", 41000, 15.0, 1400, 30.8),
    ("Old Town", 38000, 10.0, 700, 33.6),
    ("Tech Park", 25000, 18.0, 900, 31.2),
    ("Suburban North", 15000, 38.0, 1050, 28.5),
]

COLUMNS = [
    "Ward Name",
    "Population",
    "Tree Coverage",
    "Rainfall",
    "Temperature",
]


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "data" / "urban_wards.xlsx"
    out.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(DATA, columns=COLUMNS).to_excel(out, index=False)
    print(f"Created {out}")


if __name__ == "__main__":
    main()
