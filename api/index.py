import json
import os
from pathlib import Path

from flask import Flask, jsonify, send_from_directory

from .config import DEFAULT_SEASON, DEFAULT_SEASON_TYPE, SEASONS, SEASON_TYPES, snapshot_filename


app = Flask(__name__, static_folder=None)

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
DATA_DIR = Path(os.environ.get('ATS_DATA_DIR', DEFAULT_DATA_DIR))
DEFAULT_FRONTEND_DIR = Path(__file__).resolve().parents[1] / 'frontend' / 'build'
FRONTEND_DIR = Path(os.environ.get('ATS_FRONTEND_DIR', DEFAULT_FRONTEND_DIR))


def load_data(data_dir=DATA_DIR):
    """Load precomputed season data packaged with the application."""
    loaded_seasons = {season_type: {} for season_type in SEASON_TYPES}
    for season_type in SEASON_TYPES:
        for season in SEASONS:
            data_path = data_dir / snapshot_filename(season, season_type)
            with data_path.open(encoding='utf-8') as data_file:
                loaded_seasons[season_type][str(season)] = json.load(data_file)

    metadata_path = data_dir / 'metadata.json'
    with metadata_path.open(encoding='utf-8') as metadata_file:
        metadata = json.load(metadata_file)

    return loaded_seasons, metadata


season_data, data_metadata = load_data()


@app.route('/api/data')
def data():
    return jsonify({
        'season_data': season_data['regular'],
        'playoff_data': season_data['playoffs'],
        'seasons': list(SEASONS),
        'default_season': DEFAULT_SEASON,
        'default_season_type': DEFAULT_SEASON_TYPE,
        'generated_at': data_metadata['generated_at'],
    })


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'season_types': list(SEASON_TYPES),
        'generated_at': data_metadata['generated_at'],
        'seasons': list(SEASONS),
    })


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def frontend(path):
    """Serve the SvelteKit static build and its client-side routes."""
    requested_file = FRONTEND_DIR / path
    if path and requested_file.is_file():
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, 'index.html')


if __name__ == '__main__':
    app.run(debug=True)
