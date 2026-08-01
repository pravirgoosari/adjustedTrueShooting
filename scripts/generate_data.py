import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from api.analytics import get_season_data
from api.config import SEASONS


DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / 'data'


def generate_data(output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    for season in SEASONS:
        print(f"Generating {season - 1}-{str(season)[2:]} data...", flush=True)
        season_data = get_season_data(season)
        output_path = output_dir / f'{season}.json'
        output_path.write_text(
            season_data.to_json(orient='records', force_ascii=False, indent=2),
            encoding='utf-8',
        )
        print(f"Wrote {len(season_data)} players to {output_path}", flush=True)

    metadata = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'seasons': list(SEASONS),
    }
    (output_dir / 'metadata.json').write_text(
        json.dumps(metadata, indent=2) + '\n',
        encoding='utf-8',
    )


def main():
    parser = argparse.ArgumentParser(description='Generate precomputed aTS% data.')
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help='Directory for generated JSON files.',
    )
    args = parser.parse_args()
    generate_data(args.output_dir)


if __name__ == '__main__':
    main()
