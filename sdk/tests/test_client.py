import unittest
from unittest.mock import patch, MagicMock
from scraper_sre.client import ScraperObserver
import requests

class TestScraperObserver(unittest.TestCase):

    def setUp(self):
        self.observer = ScraperObserver(scraper_id="test_scraper", api_url="http://test.api")

    @patch('scraper_sre.client.requests.post')
    def test_submit_run_success(self, mock_post):
        """Test that submit_run correctly posts the current_run_data."""
        mock_response = MagicMock()
        mock_post.return_value = mock_response

        self.observer.submit_run()

        expected_url = "http://test.api/ingest"
        mock_post.assert_called_once_with(expected_url, json=self.observer.current_run_data)
        mock_response.raise_for_status.assert_called_once()

    @patch('scraper_sre.client.requests.post')
    @patch('builtins.print')
    def test_submit_run_exception(self, mock_print, mock_post):
        """Test that submit_run handles exceptions during the request."""
        error_msg = "Connection Refused"
        # Simulate an exception raised by requests.post
        mock_post.side_effect = Exception(error_msg)

        # The method should catch the exception and print an error, not raise it
        self.observer.submit_run()

        expected_url = "http://test.api/ingest"
        mock_post.assert_called_once_with(expected_url, json=self.observer.current_run_data)

        # Verify that the exception was caught and logged using print
        mock_print.assert_called_once_with(f"Failed to submit run metrics: {error_msg}")

if __name__ == '__main__':
    unittest.main()
