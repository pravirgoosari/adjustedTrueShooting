import pandas as pd
import numpy as np
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import OutputType

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
    
    def scrape_player_stats(self, season=2023):
        """Scrape player statistics using basketball-reference-web-scraper"""
        try:
            print(f"Scraping {season} NBA season stats...")
            
            # Get player stats per game
            player_stats = client.players_season_totals(season=season)
            
            # Convert to DataFrame
            df = pd.DataFrame(player_stats)
            
            # Rename columns to match our expected format
            df = df.rename(columns={
                'name': 'player_name',
                'team': 'team',
                'games_played': 'games',
                'points': 'points',
                'field_goal_attempts': 'fga',
                'free_throw_attempts': 'fta'
            })
            
            print(f"Scraped {len(df)} players")
            return df
            
        except Exception as e:
            print(f"Error scraping player stats: {str(e)}")
            return None
    
    def scrape_team_spacing(self, season=2023):
        """Scrape team 3-point shooting statistics"""
        try:
            print(f"Scraping {season} team spacing stats...")
            
            # Get team stats
            team_stats = client.teams_season_stats(season=season)
            
            # Convert to DataFrame
            df = pd.DataFrame(team_stats)
            
            # Calculate 3-point metrics
            df['team_3pa_per_game'] = df['three_point_field_goal_attempts'] / df['games_played']
            df['team_3pt_percentage'] = df['three_point_field_goals'] / df['three_point_field_goal_attempts']
            
            # Rename columns
            df = df.rename(columns={'name': 'team'})
            
            print(f"Scraped {len(df)} teams")
            return df
            
        except Exception as e:
            print(f"Error scraping team stats: {str(e)}")
            return None
