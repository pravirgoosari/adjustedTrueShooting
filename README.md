# NBA Adjusted True Shooting (aTS%)

A machine learning-powered basketball analytics platform that calculates Adjusted True Shooting Percentage (aTS%). This metric enhances traditional TS% by accounting for:
- Usage Rate (63% influence)
- Team Spacing Quality (37% influence)

## Technical Stack
- Backend: Python/Flask
- ML: scikit-learn Random Forest
- Data Processing: pandas, numpy
- Data Source: basketball-reference-web-scraper

## Features
- Random Forest regression model for predicting expected TS%
- Composite spacing score using geometric mean of 3PT% and 3PA
- Interactive data exploration across multiple NBA seasons
- Dynamic sorting and filtering capabilities

## Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 api/index.py
```

[![Deploy to Vercel](https://camo.githubusercontent.com/f209ca5cc3af7dd930b6bfc55b3d7b6a5fde1aff/68747470733a2f2f76657263656c2e636f6d2f627574746f6e)](https://vercel.com/import/project?template=https://github.com/pravirgoosari/atsml)
