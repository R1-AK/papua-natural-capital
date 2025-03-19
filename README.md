# Natural Capital Assessment (Case Study: Freeport Grasberg mine, Indonesia)

## Overview

This repository provides a comprehensive framework for assessing and valuing natural capital in Central Papua Province, Indonesia, with a critical focus on understanding the environmental impacts of mining operations, particularly in the Grasberg mine region.
![study_area_map](https://github.com/user-attachments/assets/fd0b7eff-a0b2-4c90-9503-b1da9d5d21a8)

## 🌍 Key Findings from Carbon Storage Analysis of Central Papua

### 1. Land Cover Distribution
![lulc_map_subset](https://github.com/user-attachments/assets/171a12d0-6c1b-46cc-a567-668a514622dc)
- Comprehensive analysis of 11 different land cover classes: Tree cover, shrubland, grassland, mangroves
- Tree cover identified as the dominant natural ecosystem
- Significant carbon storage capacity variations across landscape

### 2. Carbon Storage Dynamics
![carbon_comparison_bar](https://github.com/user-attachments/assets/0898a282-ffd1-4979-a581-61c7b28786fa)
- **Pristine Forest Areas**: 322.0 Mg C/ha
- **Mining Buffer Zones**: 379.6 Mg C/ha
- **Active Mining Areas**: 398.7 Mg C/ha

### 3. Economic Valuation
- Carbon Storage Value in Pristine Forests: $47,275.59/ha
- Economic Loss from Forest to Mining Conversion: $-11,251.24/ha

### 4. Restoration Potential
![restoration_potential](https://github.com/user-attachments/assets/be888738-9799-45db-b5b1-60da1701b48f)

- Potential Carbon Sequestration in Buffer Zone: -172,676,399.2 Mg C
- Estimated Restoration Value: $-25,348,895,402.35

### 5. Critical Recommendations
- Protect remaining tree cover areas
- Develop carbon financing mechanisms
- Integrate carbon values into mining impact assessments
- Establish comprehensive carbon stock monitoring system
- Focus on high-carbon storage ecosystems like mangroves

## 🔍 Project Overview

This research provides a comprehensive framework for assessing natural capital in Central Papua, focusing on:
- Quantifying ecosystem services
- Analyzing mining impacts
- Evaluating restoration scenarios
- Visualizing natural capital dynamics

## Key Methodological Approach
- Utilizes InVEST (Integrated Valuation of Ecosystem Services and Tradeoffs) models
- Interdisciplinary analysis bridging environmental science and economics
- Detailed geospatial and economic assessment
  
## Unique Contributions

1. **Quantitative Environmental Assessment**: Translates ecological changes into economic terms
2. **Scenario Modeling**: Explores potential restoration and conservation strategies
3. **Interdisciplinary Approach**: Bridges environmental science, economics, and policy

## Why This Matters

This research goes beyond traditional environmental studies by:
- Demonstrating the true economic value of intact ecosystems
- Providing a replicable methodology for natural capital assessment
- Offering concrete data to inform sustainable development decisions

## Getting Started

## Overview

This repository provides a comprehensive framework for assessing and valuing natural capital in Papua, Indonesia, with a specific focus on quantifying the impacts of mining operations (including the Grasberg mine) on ecosystem services. Using the InVEST (Integrated Valuation of Ecosystem Services and Tradeoffs) suite of models, this project demonstrates how to:

1. Quantify carbon storage across different landscapes in Papua
2. Assess the impacts of mining operations on ecosystem services
3. Evaluate potential restoration scenarios and their benefits
4. Visualize spatial patterns of natural capital

## Key Features

- **Data acquisition pipeline** for obtaining essential geospatial datasets for Papua
- **Preprocessing workflows** to prepare data for InVEST models
- **InVEST model implementations** for:
  - Carbon Storage and Sequestration
  - Habitat Quality and Biodiversity
  - Sediment Delivery Ratio
  - Water Yield
- **Scenario analysis** comparing current conditions with potential restoration scenarios
- **Economic valuation** of ecosystem services
- **Visualization tools** for creating publication-quality maps and charts

## Case Study: Mining Impacts in Papua

This repository uses the Grasberg mine region as a case study to demonstrate how natural capital assessment can quantify the environmental impacts of resource extraction. The Grasberg mine is one of the world's largest gold and copper mines, located in Papua, Indonesia, and provides an excellent example of the tensions between economic development and natural capital preservation.

## Repository Structure

```
papua-natural-capital/
│
├── data/
│   ├── raw/                          # Raw input data files
│   ├── processed/                    # Cleaned and processed datasets
│   ├── invest_inputs/                # Prepared inputs for InVEST models
│   └── results/                      # Model outputs and analysis results
│
├── notebooks/
│   ├── 01_data_acquisition.ipynb     # Data downloading and initial processing
│   ├── 02_data_preparation.ipynb     # Preparing datasets for InVEST
│   ├── 03_carbon_model.ipynb         # Carbon storage and sequestration analysis
│   ├── 04_habitat_quality.ipynb      # Biodiversity and habitat assessment
│   ├── 05_water_yield.ipynb          # Water provision services
│   ├── 06_sediment_delivery.ipynb    # Erosion and sediment retention
│   ├── 07_scenario_generation.ipynb  # Future scenario development
│   └── 08_visualization.ipynb        # Creating maps and charts
│
├── src/
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download.py               # Functions to download datasets
│   │   └── preprocess.py             # Data cleaning and formatting
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── carbon.py                 # Carbon model wrapper
│   │   ├── habitat.py                # Habitat quality model wrapper
│   │   ├── hydrology.py              # Water yield model wrapper
│   │   └── sediment.py               # Sediment delivery model wrapper
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── valuation.py              # Economic valuation functions
│   │   └── scenarios.py              # Scenario generation utilities
│   │
│   └── visualization/
│       ├── __init__.py
│       ├── maps.py                   # Functions for creating maps
│       └── charts.py                 # Functions for creating charts/graphs
│
├── environment.yml                   # Conda environment specification
├── setup.py                          # Package installation
├── README.md                         # Repository documentation
└── LICENSE                           # License information
```

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Conda (recommended for environment management)
- InVEST 3.9.0 or higher (naturalcapitalproject.org/invest/)

### Installation

1. Clone this repository:
```bash
git clone https://github.com/your-username/papua-natural-capital.git
cd papua-natural-capital
```

2. Create and activate the conda environment:
```bash
conda env create -f environment.yml
conda activate papua-natcap
```

3. Install the package in development mode:
```bash
pip install -e .
```

### Running the Analysis

Start by working through the Jupyter notebooks in numerical order:

1. Begin with data acquisition (01_data_acquisition.ipynb)
2. Proceed through model implementation notebooks
3. Finish with visualization and scenario comparison

## Sample Results

### Carbon Storage Distribution

The analysis reveals significant differences in carbon storage between pristine forest areas, mining buffer zones, and active mining areas:

- Pristine forests in Papua contain approximately 300-350 Mg C/ha
- Mining buffer zones contain approximately 100-150 Mg C/ha
- Active mining areas contain less than 50 Mg C/ha

### Economic Valuation

Using a conservative carbon price of $40 per ton CO2:

- The value of carbon storage in pristine forests is approximately $44,000/ha
- The economic loss from converting forest to mining is approximately $38,000/ha

### Restoration Potential

Restoring the buffer zones around mining operations could:

- Sequester an additional 5.2 million Mg C
- Generate approximately $764 million in carbon value
- Provide additional co-benefits for biodiversity and water regulation

## Data Sources

- **Land cover**: Ministry of Environment and Forestry Indonesia
- **Elevation**: SRTM 30m
- **Administrative boundaries**: BPS Indonesia
- **Mining concessions**: Ministry of Energy and Mineral Resources Indonesia
- **Biodiversity data**: Global Biodiversity Information Facility (GBIF)

## References

- Chaplin-Kramer, R., et al. (2019). Global modeling of nature's contributions to people. Science, 366(6462), 255-258.
- Goldstein, A., et al. (2020). Protecting irrecoverable carbon in Earth's ecosystems. Nature Climate Change, 10(4), 287-295.
- Natural Capital Project. (2019). InVEST User Guide. Stanford University.
- Sumarga, E., & Hein, L. (2016). Benefits and costs of oil palm expansion in Central Kalimantan, Indonesia, under different policy scenarios. Regional Environmental Change, 16(4), 1011-1021.


## Future Research Directions

- Expand analysis to other mining regions
- Develop more granular restoration strategies
- Create policy recommendations based on economic and ecological findings
