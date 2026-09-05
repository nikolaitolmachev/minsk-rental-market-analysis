# Minsk Rental Market Analysis

Analysis of long-term apartment rental listings in Minsk, focusing on pricing, location effects, and recorded price adjustments across different market segments.

## Minsk Districts

![Minsk administrative districts](assets/minsk_map.jpg)

*Map: Dmitry Kozhan via [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:%D0%9A%D0%B0%D1%80%D1%82%D0%B0_%D1%80%D0%B0%D0%B9%D0%BE%D0%BD%D0%BE%D0%B2_%D0%9C%D0%B8%D0%BD%D1%81%D0%BA%D0%B0.jpg), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*

## Key Findings

* The median asking rent is **$700 per month**, with a median of approximately **$12.8/m²**.

* Among districts with sufficient observations, **Central district** has the highest median monthly rent across one-, two-, and three-room apartments, while **Oktyabrsky district** has the highest median rent per square meter.

* Listings within **5 km of Independence Square** show a higher median rent per square meter than listings farther from central Minsk.

* Agency listings have a higher median monthly rent than private listings, but their median rent per square meter is nearly identical.

* **50.5%** of listings with available price history contain at least one recorded price change, and more than half of those listings were repriced multiple times.

* The **middle price segment** shows the highest repricing activity and more frequent downward price adjustments.

## Analysis

The project includes:

* data quality checks and categorical normalization;
* rental price analysis by room count and district;
* comparison of monthly rent and rent per square meter;
* location analysis using distance from Independence Square;
* comparison of apartment and seller characteristics;
* analysis of recorded price increases and decreases;
* combined district and room-count analysis;
* practical interpretation and market-oriented recommendations.

The full analysis is available in the notebook:

[`minsk_rental_market_analysis.ipynb`](minsk_rental_market_analysis.ipynb)

## Data Collection

The dataset was collected from **Realt.by** on **September 5, 2026** using a custom Python collector included in this repository.

The snapshot contains:

* **1,551 rental listings**
* **3,718 recorded price history entries**

The collector extracts structured listing and price-history data while excluding contact details, photographs, listing descriptions, and full street addresses.

A reproducible snapshot is included in the `data/` directory.

## Tech Stack

* Python
* pandas
* matplotlib
* requests
* JupyterLab

## Run Locally

Clone the repository:

```bash
git clone https://github.com/nikolaitolmachev/minsk-rental-market-analysis.git
cd minsk-rental-market-analysis
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Start JupyterLab:

```bash
jupyter lab
```

## Collector

Run a small collection as a smoke test:

```bash
python collect_realt.py --max-ads 10
```

Run the full collector:

```bash
python collect_realt.py
```

The included CSV snapshot allows the analysis to be reproduced without collecting the data again.
