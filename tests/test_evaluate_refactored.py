import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor

from wafsmith.cmd.evaluate import (
    process_payload,
    process_payloads_in_parallel,
    calculate_results,
    write_results_to_file,
    Location,
    Payload
)


def test_process_payload():
    # Test successful payload processing
    args = ("test_payload", "GET", "http://example.com", Location.URL_PARAMETERS, "test")
    
    with patch.object(Payload, 'send_request', return_value=200):
        payload_str, status_code = process_payload(args)
        assert payload_str == "test_payload"
        assert status_code == 200
    
    # Test error handling
    with patch.object(Payload, 'send_request', side_effect=Exception("Test error")):
        payload_str, status_code = process_payload(args)
        assert payload_str == "test_payload"
        assert status_code == 500  # Default error code


def test_process_payloads_in_parallel():
    payloads = ["payload1", "payload2", "payload3"]
    method = "GET"
    endpoint = "http://example.com"
    location = Location.URL_PARAMETERS
    threads = 2
    
    # Mock ThreadPoolExecutor.map to return predefined results
    mock_results = [("payload1", 200), ("payload2", 403), ("payload3", 200)]
    
    with patch('wafsmith.cmd.evaluate.ThreadPoolExecutor') as mock_executor:
        mock_instance = MagicMock()
        mock_executor.return_value.__enter__.return_value = mock_instance
        mock_instance.map.return_value = mock_results
        
        results = process_payloads_in_parallel(payloads, method, endpoint, location, threads)
        
        # Verify results are correctly organized by status code
        assert 200 in results
        assert 403 in results
        assert results[200] == ["payload1", "payload3"]
        assert results[403] == ["payload2"]


def test_calculate_results():
    # Test with some evaded payloads
    results = {
        "total": 5,
        "data": {
            200: ["payload1", "payload3"],
            403: ["payload2", "payload4", "payload5"]
        }
    }
    
    matched_count, total_count, percentage, all_passed = calculate_results(results)
    assert matched_count == 2
    assert total_count == 5
    assert percentage == 40.0
    assert all_passed is False
    
    # Test with all payloads evaded
    results = {
        "total": 3,
        "data": {
            200: ["payload1", "payload2", "payload3"]
        }
    }
    
    matched_count, total_count, percentage, all_passed = calculate_results(results)
    assert matched_count == 3
    assert total_count == 3
    assert percentage == 100.0
    assert all_passed is True
    
    # Test with no payloads evaded
    results = {
        "total": 3,
        "data": {
            403: ["payload1", "payload2", "payload3"]
        }
    }
    
    matched_count, total_count, percentage, all_passed = calculate_results(results)
    assert matched_count == 0
    assert total_count == 3
    assert percentage == 0.0
    assert all_passed is False


def test_write_results_to_file():
    payloads = ["payload1", "payload2", "payload3"]
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
    
    try:
        # Write payloads to the temporary file
        write_results_to_file(temp_path, payloads)
        
        # Verify file contents
        with open(temp_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) == 3
            assert lines[0].strip() == "payload1"
            assert lines[1].strip() == "payload2"
            assert lines[2].strip() == "payload3"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)