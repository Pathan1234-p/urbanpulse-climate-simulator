# UrbanPulse — Urban Climate Simulation Engine

Python-based ward-level climate policy simulator for urban heat risk and sustainability analysis. Built for **Pune PMC** using Hacknovate environmental datasets.

## Features

- Load ward data from Excel (population, tree coverage, rainfall, temperature)
- **Heat Risk Score** (0–100) with LOW / MEDIUM / HIGH categories
- **Sustainability Score** (0–1)
- Policy scenario simulation (trees, rainfall, temperature, population)
- Scenario comparison and ward-level recommendations
- Web dashboard for interactive planning

## Quick start

### Install

```bash
git clone https://github.com/YOUR_USERNAME/urbanpulse-climate-simulator.git
cd urbanpulse-climate-simulator
pip install -r requirements.txt
```

### CLI

```bash
# Sample data
python scripts/generate_sample_data.py
python -m climate_simulator.main

# Pune Hacknovate data (place source files in Downloads or edit paths in build script)
python scripts/build_pune_dataset.py
python -m climate_simulator.main --data data/pune_wards.xlsx
```

### Web dashboard

```bash
python web/app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Project structure

```
climate_simulator/
    data_loader.py          # Excel load & preprocessing
    pune_data_loader.py       # Hacknovate Pune dataset merger
    risk_calculator.py        # Heat risk & sustainability
    simulation_engine.py      # Policy scenarios
    recommendation_engine.py
    main.py                   # CLI entry point
web/
    app.py                    # Flask dashboard
    templates/index.html
data/
    pune_wards.xlsx           # Merged Pune PMC wards
scripts/
    build_pune_dataset.py
    generate_sample_data.py
```

## Data sources

| File | Content |
|------|---------|
| Ward-wise Population & Trees (%) | 15 PMC wards |
| Pune rainfall & temperature | IMD station 43063 (2012) |

Climate values are city-wide; ward variation uses population and tree coverage.

## Heat risk formula

Normalized inputs scaled to 0–100:

```
Heat Risk = (Temp×0.4 + Population×0.3 − Trees×0.2 − Rainfall×0.1) × 100
```

| Score | Category |
|-------|----------|
| < 30  | LOW      |
| 30–60 | MEDIUM   |
| > 60  | HIGH     |

## License

MIT
