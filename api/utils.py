import pandas as pd

def create_sample_dataset():
    """
    Create a sample dataset for testing the aTS% calculations
    """
    sample_data = {
        'player_name': ['Player A', 'Player B', 'Player C'],
        'points': [1500, 1200, 800],
        'fga': [1200, 1000, 600],
        'fta': [400, 300, 200],
        'games': [82, 75, 60],
        'team_3pa_per_game': [35.2, 28.5, 32.1],
        'team_3pt_percentage': [0.367, 0.342, 0.389]
    }
    
    return pd.DataFrame(sample_data)
