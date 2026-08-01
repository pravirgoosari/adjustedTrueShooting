import numpy as np
import pandas as pd
from basketball_reference_web_scraper import client
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from . import utils


def calculate_ts_percentage(points, fga, fta):
    """Calculate True Shooting Percentage."""
    if fga > 0 and fta > 0:
        return (points / (2 * (fga + (0.44 * fta)))) * 100
    return 0


def calculate_usage_rate(points, fga, fta, gp):
    """Calculate the usage value used by the existing aTS% model."""
    if gp > 0:
        return ((points + fga - fta) / (gp * 100)) * 100
    return 0


def get_team_abbreviation(team_name):
    """Convert a full team name to its abbreviation."""
    team_mapping = {
        'ATLANTA HAWKS': 'ATL',
        'BOSTON CELTICS': 'BOS',
        'BROOKLYN NETS': 'BKN',
        'CHARLOTTE HORNETS': 'CHA',
        'CHICAGO BULLS': 'CHI',
        'CLEVELAND CAVALIERS': 'CLE',
        'DALLAS MAVERICKS': 'DAL',
        'DENVER NUGGETS': 'DEN',
        'DETROIT PISTONS': 'DET',
        'GOLDEN STATE WARRIORS': 'GSW',
        'HOUSTON ROCKETS': 'HOU',
        'INDIANA PACERS': 'IND',
        'LOS ANGELES CLIPPERS': 'LAC',
        'LOS ANGELES LAKERS': 'LAL',
        'MEMPHIS GRIZZLIES': 'MEM',
        'MIAMI HEAT': 'MIA',
        'MILWAUKEE BUCKS': 'MIL',
        'MINNESOTA TIMBERWOLVES': 'MIN',
        'NEW ORLEANS PELICANS': 'NOP',
        'NEW YORK KNICKS': 'NYK',
        'OKLAHOMA CITY THUNDER': 'OKC',
        'ORLANDO MAGIC': 'ORL',
        'PHILADELPHIA 76ERS': 'PHI',
        'PHOENIX SUNS': 'PHX',
        'PORTLAND TRAIL BLAZERS': 'POR',
        'SACRAMENTO KINGS': 'SAC',
        'SAN ANTONIO SPURS': 'SAS',
        'TORONTO RAPTORS': 'TOR',
        'UTAH JAZZ': 'UTA',
        'WASHINGTON WIZARDS': 'WAS',
    }
    return team_mapping.get(team_name, team_name)


def format_positions(positions):
    """Keep the source's listed positions, using standard short labels."""
    abbreviations = {
        'POINT GUARD': 'PG',
        'SHOOTING GUARD': 'SG',
        'SMALL FORWARD': 'SF',
        'POWER FORWARD': 'PF',
        'CENTER': 'C',
        'GUARD': 'G',
        'FORWARD': 'F',
    }
    labels = [
        abbreviations[position.value]
        for position in positions or []
        if position is not None and position.value in abbreviations
    ]
    return '/'.join(dict.fromkeys(labels)) or '—'


def get_season_data(season_end_year):
    """Download and calculate player statistics for one season."""
    utils.safe_delay()
    stats = client.players_season_totals(season_end_year=season_end_year)

    player_totals = {}
    team_stats = {}

    for player in stats:
        name = player['name']
        team = get_team_abbreviation(player['team'].value)

        if name not in player_totals:
            player_totals[name] = {
                'games': 0,
                'minutes': 0,
                'points': 0,
                'fga': 0,
                'fta': 0,
                'team': team,
            }
        else:
            player_totals[name]['team'] = team

        # Match the listed position to the same source row used for the team.
        player_totals[name]['position'] = format_positions(player.get('positions'))

        if team not in team_stats:
            team_stats[team] = {
                'games': set(),
                'made_threes': 0,
                'attempted_threes': 0,
            }

        player_totals[name]['games'] += player['games_played']
        player_totals[name]['minutes'] += player['minutes_played']
        player_totals[name]['points'] += player['points']
        player_totals[name]['fga'] += player['attempted_field_goals']
        player_totals[name]['fta'] += player['attempted_free_throws']

        team_stats[team]['made_threes'] += player['made_three_point_field_goals']
        team_stats[team]['attempted_threes'] += player['attempted_three_point_field_goals']
        team_stats[team]['games'].add(player['games_played'])

    team_per_game = {}
    for team, totals in team_stats.items():
        games = max(totals['games'])
        if games > 0:
            team_per_game[team] = {
                '3PA': round(totals['attempted_threes'] / games, 1),
                '3PT%': round(
                    totals['made_threes'] / totals['attempted_threes'] * 100
                    if totals['attempted_threes'] > 0 else 0,
                    1,
                ),
            }

    players_data = []
    for name, totals in player_totals.items():
        games = totals['games']
        if games <= 0:
            continue

        points = totals['points']
        fga = totals['fga']
        fta = totals['fta']
        team = totals['team']
        ts = calculate_ts_percentage(points, fga, fta)
        usage_rate = calculate_usage_rate(points, fga, fta, games)

        if ts > 0 and usage_rate > 0:
            players_data.append({
                'Player': name,
                'Position': totals['position'],
                'Team': team,
                'Season': f"{season_end_year - 1}-{str(season_end_year)[2:]}",
                'PPG': round(points / games, 1),
                'MPG': totals['minutes'] / games,
                'GP': games,
                'TS%': round(ts, 1),
                'Usage Rate': round(usage_rate, 1),
                'Team 3PA': team_per_game[team]['3PA'],
                'Team 3PT%': team_per_game[team]['3PT%'],
            })

    df = pd.DataFrame(players_data)
    if df.empty:
        raise ValueError(f"No player data returned for season {season_end_year}")

    df['norm_3pa'] = (
        (df['Team 3PA'] - df['Team 3PA'].min())
        / (df['Team 3PA'].max() - df['Team 3PA'].min())
    )
    df['norm_3pt'] = (
        (df['Team 3PT%'] - df['Team 3PT%'].min())
        / (df['Team 3PT%'].max() - df['Team 3PT%'].min())
    )
    df['Spacing Score'] = np.sqrt(df['norm_3pa'] * df['norm_3pt']) * 100

    features = df[['Usage Rate', 'Spacing Score']].values
    ts_values = df['TS%'].values
    scaled_features = StandardScaler().fit_transform(features)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(scaled_features, ts_values)
    expected_ts = model.predict(scaled_features)

    adjustment_scale = np.std(df['TS%']) / np.std(ts_values - expected_ts)
    adjustments = (ts_values - expected_ts) * adjustment_scale

    df['aTS%'] = np.round(df['TS%'] + adjustments, 1)
    df['DIFF'] = np.round(df['aTS%'] - df['TS%'], 1)
    df = df.sort_values(by='PPG', ascending=False)

    return df[[
        'Player', 'Position', 'Team', 'Season', 'PPG', 'MPG', 'GP', 'aTS%', 'TS%', 'DIFF',
        'Usage Rate', 'Team 3PT%', 'Team 3PA',
    ]]
