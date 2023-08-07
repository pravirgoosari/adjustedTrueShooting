import pandas as pd
from flask import Flask, render_template
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from . import utils

app = Flask(__name__, template_folder='templates', static_folder='static')

# Set display options
pd.set_option('display.max_columns', None)
pd.set_option('display.max_rows', None)
pd.set_option('display.expand_frame_repr', False)

def calculate_ts_percentage(points, fga, fta):
    """Calculate True Shooting Percentage"""
    if fga > 0 and fta > 0:
        return (points / (2 * (fga + (0.44 * fta)))) * 100
    return 0

def calculate_usage_rate(points, fga, fta, gp):
    """Calculate Usage Rate"""
    if gp > 0:
        return ((points + fga - fta) / (gp * 100)) * 100
    return 0

def get_team_abbreviation(team_name):
    """Convert full team name to abbreviation"""
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
        'WASHINGTON WIZARDS': 'WAS'
    }
    return team_mapping.get(team_name, team_name)

def get_season_data(season_end_year=2023):
    """Get player statistics for a specific season with anti-detection measures"""
    try:
        utils.safe_delay()
        
        # Get regular season stats
        stats = client.players_season_totals(season_end_year=season_end_year)
        
        # Create dictionaries to aggregate player and team stats
        player_totals = {}
        team_stats = {}  # Track team shooting stats
        
        # First pass: aggregate totals for each player and track team stats
        for player in stats:
            name = player['name']
            team = get_team_abbreviation(player['team'].value)
            
            # Initialize or update player stats
            if name not in player_totals:
                player_totals[name] = {
                    'games': 0,
                    'points': 0,
                    'fga': 0,
                    'fta': 0,
                    'team': team
                }
            else:
                player_totals[name]['team'] = team  # Keep most recent team
            
            # Initialize or update team stats
            if team not in team_stats:
                team_stats[team] = {
                    'games': set(),  # Use set to count unique games
                    'made_threes': 0,
                    'attempted_threes': 0
                }
            
            # Add to player's totals
            player_totals[name]['games'] += player['games_played']
            player_totals[name]['points'] += player['points']
            player_totals[name]['fga'] += player['attempted_field_goals']
            player_totals[name]['fta'] += player['attempted_free_throws']
            
            # Add to team's totals
            team_stats[team]['made_threes'] += player['made_three_point_field_goals']
            team_stats[team]['attempted_threes'] += player['attempted_three_point_field_goals']
            team_stats[team]['games'].add(player['games_played'])
        
        # Calculate team per game stats
        team_per_game = {}
        for team, stats in team_stats.items():
            games = max(stats['games'])
            if games > 0:
                team_per_game[team] = {
                    '3PA': round(stats['attempted_threes'] / games, 1),
                    '3PT%': round((stats['made_threes'] / stats['attempted_threes'] * 100) if stats['attempted_threes'] > 0 else 0, 1)
                }
        
        # Create lists to store data
        players_data = []
        
        # Process aggregated player stats
        for name, totals in player_totals.items():
            games = totals['games']
            if games > 0:  # Only include players who have played games
                points = totals['points']
                fga = totals['fga']
                fta = totals['fta']
                team = totals['team']
                
                # Calculate per game averages
                ppg = points / games
                ts = calculate_ts_percentage(points, fga, fta)
                usage_rate = calculate_usage_rate(points, fga, fta, games)
                
                # Add player data
                if ts > 0 and usage_rate > 0:
                    players_data.append({
                        'Player': name,
                        'Team': team,
                        'Season': f"{season_end_year-1}-{str(season_end_year)[2:]}",
                        'PPG': round(ppg, 1),
                        'TS%': round(ts, 1),
                        'Usage Rate': round(usage_rate, 1),
                        'Team 3PA': team_per_game[team]['3PA'],
                        'Team 3PT%': team_per_game[team]['3PT%']
                    })
        
        # Create DataFrame
        df = pd.DataFrame(players_data)
        
        # Create a composite spacing score
        # Normalize both metrics to 0-1 scale first
        df['norm_3pa'] = (df['Team 3PA'] - df['Team 3PA'].min()) / (df['Team 3PA'].max() - df['Team 3PA'].min())
        df['norm_3pt'] = (df['Team 3PT%'] - df['Team 3PT%'].min()) / (df['Team 3PT%'].max() - df['Team 3PT%'].min())
        
        # Spacing score is the geometric mean of normalized 3PA and 3PT%
        # Using geometric mean because we want BOTH attempts AND percentage to be good
        df['Spacing Score'] = np.sqrt(df['norm_3pa'] * df['norm_3pt']) * 100
        
        # ML-based aTS% calculation
        # Prepare features for ML model - now using Spacing Score instead of separate 3PA and 3PT%
        X = df[['Usage Rate', 'Spacing Score']].values
        y = df['TS%'].values
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train Random Forest model
        rf_model = RandomForestRegressor(n_estimators=100, random_state=42)
        rf_model.fit(X_scaled, y)
        
        # Get predicted TS% based on features
        expected_ts = rf_model.predict(X_scaled)
        
        # Calculate adjustment based on difference from expected
        # Scale the adjustment to maintain similar range as original aTS%
        adjustment_scale = np.std(df['TS%']) / np.std(y - expected_ts)
        adjustments = (y - expected_ts) * adjustment_scale
        
        # Calculate final aTS%
        df['aTS%'] = round(df['TS%'] + adjustments, 1)
        
        # Calculate DIFF (aTS% - TS%)
        df['DIFF'] = round(df['aTS%'] - df['TS%'], 1)
        
        # Sort by PPG
        df = df.sort_values(by='PPG', ascending=False)
        
        # Reorder columns
        df = df[['Player', 'Team', 'Season', 'PPG', 'aTS%', 'TS%', 'DIFF', 'Usage Rate', 'Team 3PT%', 'Team 3PA']]
        
        return df
        
    except Exception as e:
        # Return a placeholder DataFrame with error message
        return pd.DataFrame(utils.create_error_dataframe(season_end_year, "Data Unavailable"))

@app.route('/')
def index():
    """Return 2023 season aTS% data as HTML"""
    try:
        data_2023 = get_season_data(2023)
        # Convert DataFrame to list of dictionaries for Jinja2 template
        season_data = data_2023.to_dict('records')
        return render_template('index.html', season_data=season_data)
    except Exception as e:
        return render_template('index.html', error=str(e))

if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True) 