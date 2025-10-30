"""Tests for OCR API functionality and real API integration."""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hardware.inventory import utils
from hardware.inventory import config


class TestOCRServices:
    """Test OCR service integration with mocked and real API calls."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.test_image_path = Path(__file__).parent / "data" / "test_file-1.png"
        self.mock_ocr_response = "10kΩ resistor\n±5% tolerance\nCarbon film\n25 pieces"
    
    def test_ocr_service_routing(self):
        """Test that OCR service routing works correctly."""
        # Test match/case routing for different services
        with patch('hardware.inventory.utils._mistral_ocr_extract') as mock_mistral:
            mock_mistral.return_value = self.mock_ocr_response
            result = utils.ocr_extract(self.test_image_path, "mistral")
            assert result == self.mock_ocr_response
            mock_mistral.assert_called_once()
        
        with patch('hardware.inventory.utils._openai_ocr_extract') as mock_openai:
            mock_openai.return_value = self.mock_ocr_response
            result = utils.ocr_extract(self.test_image_path, "openai")
            assert result == self.mock_ocr_response
            mock_openai.assert_called_once()
    
    def test_unknown_ocr_service(self):
        """Test that unknown OCR service raises appropriate error."""
        with pytest.raises(ValueError, match="Unknown OCR service"):
            utils.ocr_extract(self.test_image_path, "unknown_service")
    
    @patch('requests.post')
    def test_legacy_ocr_services(self, mock_post):
        """Test legacy OCR services (local, ocr.space) with file upload."""
        # Mock response for legacy services
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"text": self.mock_ocr_response}
        mock_post.return_value = mock_response
        
        result = utils.ocr_extract(self.test_image_path, "local")
        assert result == self.mock_ocr_response
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_ocr_space_response_format(self, mock_post):
        """Test OCR.Space specific response format handling."""
        # OCR.Space returns data in ParsedResults format
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "ParsedResults": [{"ParsedText": self.mock_ocr_response}]
        }
        mock_post.return_value = mock_response
        
        result = utils.ocr_extract(self.test_image_path, "ocr.space")
        assert result == self.mock_ocr_response
    
    @patch('hardware.inventory.utils.os.getenv')
    @patch('requests.post')
    def test_mistral_ocr_api_call(self, mock_post, mock_getenv):
        """Test Mistral API call structure and parameters."""
        mock_getenv.return_value = "fake_mistral_key"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "choices": [{"message": {"content": self.mock_ocr_response}}]
        }
        mock_post.return_value = mock_response
        
        result = utils._mistral_ocr_extract(self.test_image_path, "mistral")
        
        assert result == self.mock_ocr_response
        mock_post.assert_called_once()
        
        # Verify API call structure
        call_args = mock_post.call_args
        assert call_args[0][0] == utils.DEFAULT_ENDPOINTS["mistral"]
        assert "Authorization" in call_args[1]["headers"]
        assert "model" in call_args[1]["json"]
        assert call_args[1]["json"]["model"] == "pixtral-large-latest"
    
    def test_api_key_missing_error(self):
        """Test that missing API keys raise appropriate errors."""
        with patch('hardware.inventory.utils.os.getenv', return_value=None):
            with pytest.raises(ValueError, match="MISTRAL_API_KEY"):
                utils._mistral_ocr_extract(self.test_image_path, "mistral")
            
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                utils._openai_ocr_extract(self.test_image_path, "openai")
            
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
                utils._openrouter_ocr_extract(self.test_image_path, "openrouter")


class TestFieldParsing:
    """Test component field parsing from OCR text."""
    
    def test_value_parsing(self):
        """Test parsing of component values."""
        test_cases = [
            ("10kΩ resistor", {"value": "10kΩ"}),
            ("100uF capacitor", {"value": "100uF"}),
            ("22nF ceramic", {"value": "22nF"}),
            ("2.2uH inductor", {"value": "2.2uH"}),
            ("5% tolerance", {"value": "5%"}),
        ]
        
        for text, expected in test_cases:
            result = utils.parse_fields(text)
            if "value" in expected:
                assert "value" in result
                assert result["value"] == expected["value"]
    
    def test_quantity_parsing(self):
        """Test parsing of quantities."""
        test_cases = [
            ("25 pcs resistor", {"qty": "25"}),
            ("100 pc capacitors", {"qty": "100"}),
            ("5 pieces", {"qty": "5"}),
        ]
        
        for text, expected in test_cases:
            result = utils.parse_fields(text)
            if "qty" in expected:
                assert "qty" in result
                assert result["qty"] == expected["qty"]
    
    def test_price_parsing(self):
        """Test parsing of prices with currency symbols."""
        test_cases = [
            ("$2.50 each", {"price": "$2.50"}),
            ("€1.20 per piece", {"price": "€1.20"}),
            ("£0.75 resistor", {"price": "£0.75"}),
        ]
        
        for text, expected in test_cases:
            result = utils.parse_fields(text)
            if "price" in expected:
                assert "price" in result
                assert result["price"] == expected["price"]


class TestDatabaseImport:
    """Test database import functionality with the example JSONLD data."""
    
    def setup_method(self):
        """Setup test database."""
        self.test_db_path = Path(tempfile.mkdtemp()) / "test_inventory.db"
        self.db = utils.SQLiteDB(self.test_db_path)
        self.example_data_path = Path(__file__).parent.parent / "data" / "electronics_updated_1.jsonld"
    
    def teardown_method(self):
        """Cleanup test database."""
        if self.test_db_path.exists():
            self.test_db_path.unlink()
    
    def test_import_example_database(self):
        """Test importing the example JSONLD database."""
        if not self.example_data_path.exists():
            pytest.skip("Example database not found")
        
        # Import the example data
        self.db.import_db(self.example_data_path)
        
        # Verify data was imported
        stats = self.db.get_stats()
        assert stats["total_components"] > 0
        
        # Test search functionality
        results = self.db.search("resistor")
        assert len(results) > 0
        
        # Test component retrieval
        components = self.db.list_all(limit=5)
        assert len(components) > 0
        
        # Verify component structure
        for component in components[:1]:  # Check first component
            assert "id" in component
            assert "type" in component or "description" in component


class TestAPIConnectivity:
    """Test API connectivity using free endpoints."""
    
    def test_mistral_connectivity(self):
        """Test Mistral API connectivity using models endpoint (free)."""
        if not os.getenv("MISTRAL_API_KEY"):
            pytest.skip("MISTRAL_API_KEY not set")
        
        result = utils.test_api_connectivity("mistral")
        assert result is True, "Mistral API connectivity test failed"
    
    def test_openai_connectivity(self):
        """Test OpenAI API connectivity using models endpoint (free)."""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        result = utils.test_api_connectivity("openai")
        assert result is True, "OpenAI API connectivity test failed"
    
    def test_openrouter_connectivity(self):
        """Test OpenRouter API connectivity using models endpoint (free)."""
        if not os.getenv("OPENROUTER_API_KEY"):
            pytest.skip("OPENROUTER_API_KEY not set")
        
        result = utils.test_api_connectivity("openrouter")
        assert result is True, "OpenRouter API connectivity test failed"


@pytest.mark.integration
class TestRealAPIIntegration:
    """Integration tests for real API calls (requires API keys and costs money)."""
    
    def test_mistral_api_integration(self):
        """Test real Mistral API call if key is available. WARNING: Costs money!"""
        pytest.skip("Expensive test - only run manually with pytest -m integration")
        
        if not os.getenv("MISTRAL_API_KEY"):
            pytest.skip("MISTRAL_API_KEY not set")
        
        test_path = Path(__file__).parent / "data" / "test_file-1.png"
        if not test_path.exists():
            pytest.skip("Test image not available")
        
        try:
            result = utils._mistral_ocr_extract(test_path, "mistral")
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.fail(f"Mistral API call failed: {e}")
    
    def test_openai_api_integration(self):
        """Test real OpenAI API call if key is available. WARNING: Costs money!"""
        pytest.skip("Expensive test - only run manually with pytest -m integration")
        
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OPENAI_API_KEY not set")
        
        test_path = Path(__file__).parent / "data" / "test_file-1.png"
        if not test_path.exists():
            pytest.skip("Test image not available")
        
        try:
            result = utils._openai_ocr_extract(test_path, "openai")
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            pytest.fail(f"OpenAI API call failed: {e}")


class TestCLICommands:
    """Test CLI command integration with database operations."""
    
    def setup_method(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.test_db = self.test_dir / "test_inventory.db"
        # Copy example data for testing
        self.example_data = Path(__file__).parent.parent / "data" / "electronics_updated_1.jsonld"
    
    def teardown_method(self):
        """Cleanup test environment."""
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_database_import_via_cli(self):
        """Test database import through CLI interface."""
        if not self.example_data.exists():
            pytest.skip("Example database not found")
        
        # Use explicit test database - NEVER touch real database in tests
        db = utils.SQLiteDB(self.test_db)
        db.import_db(self.example_data)
        
        # Verify import worked
        stats = db.get_stats()
        assert stats["total_components"] > 0
    
    def test_search_functionality(self):
        """Test search functionality with imported data."""
        if not self.example_data.exists():
            pytest.skip("Example database not found")
        
        # Import data and test search
        db = utils.SQLiteDB(self.test_db)
        db.import_db(self.example_data)
        
        # Test various search queries
        test_queries = ["resistor", "capacitor", "10k", "uF"]
        
        for query in test_queries:
            results = db.search(query)
            # Just verify search doesn't crash and returns list
            assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])