import unittest

from api.index import app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_serves_svelte_app(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'/_app/immutable/', response.data)
        response.close()

    def test_data_api_returns_all_seasons(self):
        response = self.client.get('/api/data')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['seasons'], [2026, 2025, 2024, 2023])
        self.assertEqual(response.json['default_season'], 2026)
        for season in ('2026', '2025', '2024', '2023'):
            self.assertIn(season, response.json['season_data'])
            for player in response.json['season_data'][season]:
                self.assertIn('Position', player)
                self.assertIn('MPG', player)
                self.assertIsInstance(player['MPG'], (int, float))
                self.assertGreaterEqual(player['MPG'], 0)
                self.assertIn('GP', player)
                self.assertIsInstance(player['GP'], int)
                self.assertGreater(player['GP'], 0)
                self.assertRegex(player['Position'], r'^(PG|SG|SF|PF|C|G|F)(/(PG|SG|SF|PF|C|G|F))*$|^—$')

    def test_health_reports_precomputed_data(self):
        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'ok')
        self.assertEqual(response.json['seasons'], [2026, 2025, 2024, 2023])
        self.assertEqual(response.json['season_types'], ['regular', 'playoffs'])

    def test_playoff_data_is_available_and_separate(self):
        response = self.client.get('/api/data')
        self.assertEqual(response.json['default_season_type'], 'regular')
        for season in ('2026', '2025', '2024', '2023'):
            rows = response.json['playoff_data'][season]
            self.assertTrue(rows)
            self.assertNotEqual(rows, response.json['season_data'][season])
            for player in rows:
                self.assertGreater(player['GP'], 0)
                self.assertGreaterEqual(player['MPG'], 0)
                self.assertIsInstance(player['aTS%'], (int, float))
                self.assertEqual(player['Season'], f'{int(season)-1}-{season[2:]}')


if __name__ == '__main__':
    unittest.main()
