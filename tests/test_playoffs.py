import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from api.analytics import get_season_data, parse_playoff_totals
from api.config import snapshot_filename
from scripts.generate_data import generate_data


def totals_page(legacy=True):
    names = ('player', 'team_id', 'g', 'gs') if legacy else (
        'name_display', 'team_name_abbr', 'games', 'games_started')
    rows = []
    for name, team, games, minutes, points, fga, threes, threes_attempted in (
        ('Player One', 'BOS', 4, 125, 100, 70, 10, 30),
        ('Player Two', 'LAL', 6, 185, 155, 110, 12, 45),
        ('Player Three', 'OKC', 8, 220, 140, 115, 14, 50),
        ('Player Four', 'DEN', 10, 320, 300, 185, 30, 65),
    ):
        fields = {names[0]: name, names[1]: team, names[2]: games,
                  names[3]: games, 'pos': 'PG', 'mp': minutes, 'pts': points,
                  'fga': fga, 'fta': 25, 'fg3': threes, 'fg3a': threes_attempted}
        rows.append('<tr>' + ''.join(
            f'<td data-stat="{key}">{value}</td>' for key, value in fields.items()
        ) + '</tr>')
    return '<table id="totals_stats"><tbody>' + ''.join(rows) + '</tbody></table>'


class PlayoffDataTests(unittest.TestCase):
    def test_legacy_and_current_field_names(self):
        for legacy in (True, False):
            with self.subTest(legacy=legacy):
                rows = parse_playoff_totals(totals_page(legacy))
                self.assertEqual(len(rows), 4)
                self.assertEqual(rows[0]['name'], 'Player One')
                self.assertEqual(rows[0]['team'].value, 'BOSTON CELTICS')
                self.assertEqual(rows[0]['games_played'], 4)
                self.assertEqual(rows[0]['minutes_played'], 125)

    def test_missing_or_invalid_totals_fail_explicitly(self):
        for content in ('<html>Unavailable</html>', totals_page().replace('BOS', 'INVALID')):
            with self.subTest(content=content[:30]), self.assertRaises(ValueError):
                parse_playoff_totals(content)

    @patch('api.analytics.utils.safe_delay')
    @patch('api.analytics.get_playoff_totals')
    @patch('api.analytics.client.players_season_totals')
    def test_regular_and_playoffs_use_separate_sources(self, regular, playoffs, delay):
        regular.return_value = parse_playoff_totals(totals_page())
        playoffs.return_value = parse_playoff_totals(totals_page().replace('Player One', 'Playoff Only'))
        result = get_season_data(2026, season_type='playoffs')
        playoffs.assert_called_once_with(2026)
        regular.assert_not_called()
        player = result.set_index('Player').loc['Playoff Only']
        self.assertEqual(player['GP'], 4)
        self.assertEqual(player['MPG'], 31.25)
        self.assertEqual(player['PPG'], 25.0)
        self.assertFalse(result.isna().any().any())
        regular_result = get_season_data(2026)
        regular.assert_called_once_with(season_end_year=2026)
        self.assertIn('Player One', regular_result['Player'].values)
        self.assertNotIn('Playoff Only', regular_result['Player'].values)

    def test_unknown_type_rejected(self):
        with self.assertRaises(ValueError):
            get_season_data(2026, 'invalid')
        with self.assertRaises(ValueError):
            snapshot_filename(2026, 'invalid')

    @patch('scripts.generate_data.SEASONS', (2026,))
    @patch('scripts.generate_data.get_season_data')
    def test_generator_packages_both_types(self, calculate):
        calculate.side_effect = lambda year, season_type: pd.DataFrame([{'type': season_type}])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generate_data(output)
            self.assertEqual(json.loads((output / '2026.json').read_text()), [{'type': 'regular'}])
            self.assertEqual(json.loads((output / '2026_playoffs.json').read_text()), [{'type': 'playoffs'}])
            metadata = json.loads((output / 'metadata.json').read_text())
            self.assertEqual(metadata['season_types'], ['regular', 'playoffs'])


if __name__ == '__main__':
    unittest.main()
