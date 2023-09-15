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
## Deployment
- Hosted at [adjustedtrueshooting.com](https://www.adjustedtrueshooting.com/)
- Used GitHub Actions to containerize and push Docker images to DockerHub
- Deployed with Azure App Service via automated CI/CD pipeline