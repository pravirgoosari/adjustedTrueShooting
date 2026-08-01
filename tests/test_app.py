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


if __name__ == '__main__':
    unittest.main()
