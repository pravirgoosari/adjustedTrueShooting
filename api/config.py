SEASONS = (2026, 2025, 2024, 2023)
DEFAULT_SEASON = SEASONS[0]
SEASON_TYPES = {'regular': 'Regular Season', 'playoffs': 'Playoffs'}
DEFAULT_SEASON_TYPE = 'regular'


def snapshot_filename(season, season_type):
    if season_type not in SEASON_TYPES:
        raise ValueError(f'Unknown season type: {season_type}')
    suffix = '_playoffs' if season_type == 'playoffs' else ''
    return f'{season}{suffix}.json'
