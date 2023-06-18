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
