# NBA Adjusted True Shooting (aTS%)

A machine learning-powered basketball analytics platform that calculates Adjusted True Shooting Percentage (aTS%). This metric enhances traditional TS% by accounting for:
- Usage Rate (63% influence)
- Team Spacing Quality (37% influence)

## Technical Stack
- Frontend: SvelteKit, TypeScript
- Backend/API: Python/Flask
- ML: scikit-learn Random Forest
- Data Processing: pandas, numpy
- Data Source: basketball-reference-web-scraper

## Features
- Random Forest regression model for predicting expected TS%
- Composite spacing score using geometric mean of 3PT% and 3PA
- Interactive data exploration across multiple NBA seasons
- Regular-season and playoff datasets, with a Type selector (Regular Season by default)
- Dynamic sorting and filtering capabilities

## Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m scripts.generate_data

cd frontend
npm install
npm run build
cd ..

python3 -m api.index
```

For frontend development with hot reload, run `npm run dev` from `frontend/`
while Flask is running on port 5000. Vite proxies API requests to Flask.

Season data is generated before the web process starts and stored in `data/`.
The production container only loads these precomputed snapshots, keeping cold
starts fast and avoiding live scraping during requests.

`python -m scripts.generate_data` generates both types for every configured year:
`data/2026.json` contains regular-season stats and `data/2026_playoffs.json`
contains playoff stats (likewise for other years). aTS% is calculated separately
for each dataset. Regenerate both types before restarting the backend after this
update; the existing GitHub Actions generation step includes both automatically.
The API keeps regular-season results in `season_data` and adds `playoff_data`.
## Deployment
- Hosted at [adjustedtrueshooting.com](https://www.adjustedtrueshooting.com/)
- Used GitHub Actions to containerize and push Docker images to DockerHub
- Deployed with Azure App Service via automated CI/CD pipeline
