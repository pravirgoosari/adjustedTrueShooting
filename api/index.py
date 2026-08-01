import json
import os
from pathlib import Path

from flask import Flask, jsonify, render_template

from .config import DEFAULT_SEASON, SEASONS


app = Flask(__name__, template_folder='templates', static_folder='static')

DEFAULT_DATA_DIR = Path(__file__).resolve().parents[1] / 'data'
DATA_DIR = Path(os.environ.get('ATS_DATA_DIR', DEFAULT_DATA_DIR))


def load_data(data_dir=DATA_DIR):
    """Load precomputed season data packaged with the application."""
    loaded_seasons = {}
    for season in SEASONS:
        data_path = data_dir / f'{season}.json'
        with data_path.open(encoding='utf-8') as data_file:
            loaded_seasons[str(season)] = json.load(data_file)

    metadata_path = data_dir / 'metadata.json'
    with metadata_path.open(encoding='utf-8') as metadata_file:
        metadata = json.load(metadata_file)

    return loaded_seasons, metadata


season_data, data_metadata = load_data()


@app.route('/')
def index():
    return render_template(
        'index.html',
        season_data=season_data,
        seasons=SEASONS,
        default_season=DEFAULT_SEASON,
        data_generated_at=data_metadata['generated_at'],
    )


@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'generated_at': data_metadata['generated_at'],
        'seasons': list(SEASONS),
    })


if __name__ == '__main__':
    app.run(debug=True)
