import unittest

from api.index import app


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_renders_all_seasons(self):
        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        for season in (2026, 2025, 2024, 2023):
            self.assertIn(f'data-season="{season}"'.encode(), response.data)

    def test_health_reports_precomputed_data(self):
        response = self.client.get('/health')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'ok')
        self.assertEqual(response.json['seasons'], [2026, 2025, 2024, 2023])


if __name__ == '__main__':
    unittest.main()
