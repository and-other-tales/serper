import unittest
from unittest.mock import patch, MagicMock
import sys
import os
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).parent.parent))

from web.crawler import WebCrawler


class TestWebCrawler(unittest.TestCase):
    
    def test_crawler_initialization(self):
        """Test that the crawler initializes correctly."""
        crawler = WebCrawler()
        self.assertEqual(crawler.rate_limit_delay, 2.0)
        self.assertTrue(crawler.respect_robots_txt)
        
    @patch('web.crawler.requests.get')
    def test_robots_txt_parsing(self, mock_get):
        """Test that robots.txt is parsed correctly."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        User-agent: *
        Disallow: /private/
        Allow: /public/
        """
        mock_get.return_value = mock_response
        
        crawler = WebCrawler()
        url = "https://example.com/page.html"
        
        # First call should initialize the parser
        result = crawler._can_fetch(url)
        self.assertTrue(result)
        
        # Test disallowed URL
        disallowed_url = "https://example.com/private/page.html"
        result = crawler._can_fetch(disallowed_url)
        self.assertFalse(result)
        
    @patch('web.crawler.BeautifulSoup')
    @patch('web.crawler.requests.get')
    def test_fetch_with_requests(self, mock_get, mock_bs):
        """Test fetching a page with requests."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response
        
        # Mock BeautifulSoup
        mock_soup = MagicMock()
        mock_bs.return_value = mock_soup
        
        crawler = WebCrawler(use_playwright=False)
        
        # Bypass robots.txt check
        crawler._can_fetch = MagicMock(return_value=True)
        
        # Test fetch_page
        html, soup = crawler._fetch_with_requests("https://example.com/page.html")
        
        self.assertEqual(html, "<html><body>Test content</body></html>")
        self.assertEqual(soup, mock_soup)
        
    @patch('web.crawler.tempfile.mkstemp')
    def test_save_content(self, mock_mkstemp):
        """Test saving content to a temporary file."""
        # Mock tempfile
        mock_fd = 123
        mock_path = "/tmp/serper_test.html"
        mock_mkstemp.return_value = (mock_fd, mock_path)
        
        # Mock os.fdopen
        mock_file = MagicMock()
        mock_open = MagicMock(return_value=mock_file)
        
        with patch('web.crawler.os.fdopen', mock_open):
            crawler = WebCrawler()
            html = "<html><body>Test content</body></html>"
            url = "https://example.com/page.html"
            
            path = crawler.save_content(html, url)
            
            self.assertEqual(path, mock_path)
            self.assertIn(mock_path, crawler.temp_files)
            mock_file.write.assert_called_once_with(html)
            
    @patch('web.crawler.BeautifulSoup')
    def test_extract_links(self, mock_bs):
        """Test extracting links from HTML."""
        # Create mock soup and tags
        mock_soup = MagicMock()
        mock_tag1 = MagicMock()
        mock_tag1["href"] = "/relative/link.html"
        mock_tag2 = MagicMock()
        mock_tag2["href"] = "https://example.com/absolute/link.html"
        mock_tag3 = MagicMock()
        mock_tag3["href"] = "ftp://invalid.com/invalid.html"  # Non-http(s) link
        mock_tag4 = MagicMock()
        mock_tag4["href"] = "https://example.com/absolute/link.html#fragment"  # With fragment
        
        mock_soup.find_all.return_value = [mock_tag1, mock_tag2, mock_tag3, mock_tag4]
        
        crawler = WebCrawler()
        base_url = "https://example.com/base.html"
        
        links = crawler.extract_links(mock_soup, base_url)
        
        # Should extract both links, removing fragment from one
        self.assertEqual(len(links), 2)
        self.assertIn("https://example.com/relative/link.html", links)
        self.assertIn("https://example.com/absolute/link.html", links)
        
        # Should not include fragment or non-http(s) links
        for link in links:
            self.assertFalse("#" in link)
            self.assertTrue(link.startswith(("http://", "https://")))


if __name__ == "__main__":
    unittest.main()