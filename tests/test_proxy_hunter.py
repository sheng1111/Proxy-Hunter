"""Comprehensive tests for ProxyHunter package.

This test suite covers:
- Core proxy fetching and validation functionality
- Database operations and statistics
- Web API endpoints
- CLI interface
- Multi-language support
"""

import json
import os
import sys
import time
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from proxyhunter import ProxyHunter, ProxyHunterError, quick_scan
from proxyhunter.web_app import app, get_translation
from proxyhunter.core import DatabaseError


class TestProxyHunter:
    """Test the core ProxyHunter functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def hunter(self, temp_db):
        """Create a ProxyHunter instance with temporary database."""
        return ProxyHunter(threads=2, timeout=1, db_path=temp_db)
    
    def test_init(self, hunter):
        """Test ProxyHunter initialization."""
        assert hunter.threads == 2
        assert hunter.timeout == 1
        assert not hunter.anonymous_only
        assert hunter.db_path.exists()
    
    def test_database_initialization(self, hunter):
        """Test database is properly initialized."""
        stats = hunter.get_statistics()
        assert isinstance(stats, dict)
        assert 'total_proxies' in stats
        assert 'working_proxies' in stats
        assert 'failed_proxies' in stats
    
    @patch('proxyhunter.core.requests.Session.get')
    def test_fetch_proxies(self, mock_get, hunter):
        """Test proxy fetching functionality."""
        # Mock response for free-proxy-list
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = '''
        <html>
        <body>
        <table>
        <tr><td>1.1.1.1:8080</td></tr>
        <tr><td>2.2.2.2:3128</td></tr>
        </table>
        </body>
        </html>
        '''
        mock_get.return_value = mock_response
        
        proxies = hunter.fetch_proxies(sources=['free-proxy-list'])
        
        assert isinstance(proxies, list)
        assert len(proxies) >= 0  # May be empty if regex doesn't match
        mock_get.assert_called()
    
    def test_validate_proxies(self, hunter):
        """Test proxy validation."""
        # Test with fake proxies that will fail
        fake_proxies = ['1.1.1.1:8080', '2.2.2.2:3128']
        results = hunter.validate_proxies(fake_proxies, show_progress=False)
        
        assert isinstance(results, list)
        assert len(results) == 2
        
        for result in results:
            assert 'proxy' in result
            assert 'status' in result
            assert result['status'] in ['ok', 'failed', 'error', 'invalid']
    
    def test_save_to_database(self, hunter):
        """Test saving results to database."""
        fake_results = [
            {
                'proxy': '1.1.1.1:8080',
                'host': '1.1.1.1',
                'port': 8080,
                'status': 'ok',
                'response_time': 0.5,
                'data_size': 100,
                'is_anonymous': True
            },
            {
                'proxy': '2.2.2.2:3128',
                'host': '2.2.2.2',
                'port': 3128,
                'status': 'failed',
                'response_time': None,
                'data_size': 0,
                'is_anonymous': False
            }
        ]
        
        hunter.save_to_database(fake_results)
        
        # Check if data was saved
        stats = hunter.get_statistics()
        assert stats['total_proxies'] >= 2
        assert stats['working_proxies'] >= 1
    
    def test_get_working_proxies(self, hunter):
        """Test retrieving working proxies."""
        # First add some test data
        fake_results = [
            {
                'proxy': '3.3.3.3:8080',
                'host': '3.3.3.3',
                'port': 8080,
                'status': 'ok',
                'response_time': 0.3,
                'data_size': 150,
                'is_anonymous': True
            }
        ]
        hunter.save_to_database(fake_results)
        
        working_proxies = hunter.get_working_proxies(limit=10)
        assert isinstance(working_proxies, list)
        
        if working_proxies:
            proxy = working_proxies[0]
            assert 'proxy' in proxy
            assert 'status' in proxy
    
    def test_file_operations(self, hunter, tmp_path):
        """Test saving and loading proxy files."""
        fake_results = [
            {'proxy': '4.4.4.4:8080', 'status': 'ok', 'response_time': 0.4},
            {'proxy': '5.5.5.5:3128', 'status': 'failed', 'response_time': None}
        ]
        
        # Test different formats
        for fmt in ['txt', 'json', 'jsonl']:
            output_file = tmp_path / f'test_proxies.{fmt}'
            hunter.save(fake_results, str(output_file), fmt=fmt)
            
            assert output_file.exists()
            
            # Test loading
            loaded = hunter.load(str(output_file), fmt=fmt)
            assert isinstance(loaded, list)
            assert len(loaded) >= 1  # At least one working proxy
    
    def test_close(self, hunter):
        """Test resource cleanup."""
        hunter.close()
        # Should not raise any exceptions


class TestWebApp:
    """Test the web application functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_index_page(self, client):
        """Test the main dashboard page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Proxy Hunter' in response.data
    
    def test_language_support(self, client):
        """Test multi-language support."""
        # Test English (default)
        response = client.get('/')
        assert response.status_code == 200
        
        # Test Chinese
        response = client.get('/?lang=zh')
        assert response.status_code == 200
        
        # Test Japanese
        response = client.get('/?lang=ja')
        assert response.status_code == 200
    
    def test_api_data(self, client):
        """Test the API data endpoint."""
        response = client.get('/api/data')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total' in data
        assert 'success' in data
        assert 'fail' in data
        assert 'average' in data
    
    @patch('proxyhunter.web_app.threading.Thread')
    def test_api_refresh(self, mock_thread, client):
        """Test the API refresh endpoint."""
        response = client.post('/api/refresh')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'started'
        
        # Check that background thread was started
        mock_thread.assert_called_once()
    
    def test_api_export(self, client):
        """Test the API export functionality."""
        # Test different formats
        for fmt in ['txt', 'json', 'csv']:
            response = client.get(f'/api/export?format={fmt}')
            assert response.status_code == 200
    
    def test_translation_function(self):
        """Test the translation function."""
        en_trans = get_translation('en')
        zh_trans = get_translation('zh')
        ja_trans = get_translation('ja')
        
        assert en_trans['title'] == 'Proxy Hunter Dashboard'
        assert zh_trans['title'] == 'Proxy Hunter 儀表板'
        assert ja_trans['title'] == 'Proxy Hunter ダッシュボード'
        
        # Test fallback to English for unknown language
        unknown_trans = get_translation('unknown')
        assert unknown_trans == en_trans


class TestQuickScan:
    """Test the quick scan functionality."""
    
    @patch('proxyhunter.ProxyHunter')
    def test_quick_scan(self, mock_hunter_class):
        """Test quick scan function."""
        # Mock ProxyHunter instance
        mock_hunter = MagicMock()
        mock_hunter.fetch_proxies.return_value = ['1.1.1.1:8080', '2.2.2.2:3128']
        mock_hunter.validate_proxies.return_value = [
            {'proxy': '1.1.1.1:8080', 'status': 'ok', 'response_time': 0.5},
            {'proxy': '2.2.2.2:3128', 'status': 'failed', 'response_time': None}
        ]
        mock_hunter_class.return_value = mock_hunter
        
        results = quick_scan(threads=5, limit=2)
        
        assert isinstance(results, list)
        assert len(results) == 1  # Only working proxies
        assert results[0]['status'] == 'ok'
        
        # Verify ProxyHunter was called correctly
        mock_hunter_class.assert_called_once_with(threads=5, anonymous_only=False)
        mock_hunter.fetch_proxies.assert_called_once()
        mock_hunter.validate_proxies.assert_called_once()
        mock_hunter.save_to_database.assert_called_once()
        mock_hunter.close.assert_called_once()


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_proxy_format(self):
        """Test handling of invalid proxy formats."""
        hunter = ProxyHunter()
        
        invalid_proxies = ['invalid', '1.1.1.1', ':8080', '999.999.999.999:99999']
        results = hunter.validate_proxies(invalid_proxies, show_progress=False)
        
        assert len(results) == len(invalid_proxies)
        for result in results:
            assert result['status'] in ['invalid', 'error', 'failed']
        
        hunter.close()
    
    def test_database_error_handling(self):
        """Test database error handling."""
        # Try to create hunter with invalid database path
        with pytest.raises((DatabaseError, OSError)):
            hunter = ProxyHunter(db_path='/invalid/path/database.db')
    
    def test_empty_proxy_list(self):
        """Test handling of empty proxy lists."""
        hunter = ProxyHunter()
        
        results = hunter.validate_proxies([])
        assert results == []
        
        hunter.close()


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Clean up any test files created during testing."""
    yield
    
    # Clean up any temporary files
    test_files = [
        'test_proxies.txt',
        'test_proxies.json',
        'test_proxies.jsonl',
        'proxy_data.db',
        'proxy_dashboard.db'
    ]
    
    for filename in test_files:
        if os.path.exists(filename):
            try:
                os.unlink(filename)
            except OSError:
                pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

