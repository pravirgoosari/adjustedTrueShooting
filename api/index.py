import pandas as pd
import numpy as np

class AdjustedTrueShooting:
    """
    Calculate Adjusted True Shooting Percentage (aTS%) using usage rate and team spacing.
    """
    
    def __init__(self):
        pass
        
    def calculate_usage_rate(self, points, fga, fta, games):
        """
        Calculate usage rate: (Points + FGA - FTA) / (Games × 100)
        """
        if games == 0:
            return 0.0
        return (points + fga - fta) / (games * 100)
    
    def calculate_spacing_score(self, team_3pa_per_game, team_3pt_percentage):
        """
        Calculate team spacing score using geometric mean of normalized 3PA and 3PT%
        """
        # Normalize 3PA (assuming range 20-45 attempts per game)
        normalized_3pa = np.clip((team_3pa_per_game - 20) / (45 - 20), 0, 1)
        
        # 3PT% is already 0-1, but ensure it's reasonable (0.3-0.45)
        normalized_3pt = np.clip((team_3pt_percentage - 0.3) / (0.45 - 0.3), 0, 1)
        
        # Geometric mean for spacing score
        spacing_score = np.sqrt(normalized_3pa * normalized_3pt)
        return spacing_score
    
    def calculate_true_shooting_percentage(self, points, fga, fta):
        """
        Calculate traditional True Shooting Percentage
        """
        if fga + (0.44 * fta) == 0:
            return 0.0
        return points / (2 * (fga + 0.44 * fta))
    
    def calculate_adjusted_ts_percentage(self, player_stats):
        """
        Calculate aTS% for a player using the 50% usage, 50% spacing formula
        
        Formula: aTS% = TS% + (Usage Factor × 0.5) + (Spacing Factor × 0.5)
        """
        # Extract player stats
        points = player_stats['points']
        fga = player_stats['fga']
        fta = player_stats['fta']
        games = player_stats['games']
        team_3pa_per_game = player_stats['team_3pa_per_game']
        team_3pt_percentage = player_stats['team_3pt_percentage']
        
        # Calculate base metrics
        usage_rate = self.calculate_usage_rate(points, fga, fta, games)
        spacing_score = self.calculate_spacing_score(team_3pa_per_game, team_3pt_percentage)
        ts_percentage = self.calculate_true_shooting_percentage(points, fga, fta)
        
        # Calculate adjustment factors
        # Usage factor: higher usage = positive adjustment (more impressive)
        usage_factor = (usage_rate - 0.25) * 0.1  # Normalize around 25% usage
        
        # Spacing factor: better spacing = negative adjustment (less impressive)
        spacing_factor = (0.5 - spacing_score) * 0.05  # Normalize around 0.5 spacing
        
        adjustment = (usage_factor * 0.5) + (spacing_factor * 0.5)
        
        # Calculate final aTS%
        adjusted_ts = ts_percentage + adjustment
        
        return {
            'player_name': player_stats.get('player_name', 'Unknown'),
            'actual_ts': ts_percentage,
            'usage_rate': usage_rate,
            'spacing_score': spacing_score,
            'usage_factor': usage_factor,
            'spacing_factor': spacing_factor,
            'adjustment': adjustment,
            'adjusted_ts': adjusted_ts
        }
