import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wafsmith.cmd.evaluate import evaluate, EvaluateConfig, TestingEnv


@pytest.fixture
def mock_config():
    config = EvaluateConfig(
        setup_dir="/tmp/test-infra/",
        output_evaded_path="/tmp/evaded.txt",
        attack_payloads_dir="/tmp/payloads/",
        traffic_payloads_dir="/tmp/traffic/",
    )
    config.attack_payloads = ["payload1", "payload2", "payload3"]
    config.traffic_payloads = ["traffic1", "traffic2"]
    return config


@pytest.fixture
def mock_testing_env():
    with patch("wafsmith.cmd.evaluate.TestingEnv") as mock_env_class:
        mock_env = MagicMock()
        mock_env_class.return_value = mock_env
        yield mock_env

@pytest.fixture
def mock_requests():
    with patch("wafsmith.cmd.evaluate.requests") as mock_requests:
        # Create mock response objects
        mock_response_403 = MagicMock()
        mock_response_403.status_code = 403
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        
        # Configure the mock get and post methods
        def mock_get(url, headers=None, params=None):
            if params and "payload" in params:
                if params["payload"] in ["payload1", "payload3"]:
                    return mock_response_403
                elif params["payload"] == "payload2":
                    return mock_response_200
                elif "traffic" in params["payload"]:
                    return mock_response_200
            return mock_response_403
        
        def mock_post(url, headers=None, data=None):
            if data and "payload" in data:
                if data["payload"] in ["payload1", "payload3"]:
                    return mock_response_403
                elif data["payload"] == "payload2":
                    return mock_response_200
                elif "traffic" in data["payload"]:
                    return mock_response_200
            return mock_response_403
        
        mock_requests.get.side_effect = mock_get
        mock_requests.post.side_effect = mock_post
        
        yield mock_requests


@patch("wafsmith.cmd.evaluate.console")
@patch("wafsmith.cmd.evaluate.time.sleep")
@patch("wafsmith.cmd.evaluate.open")
@patch("builtins.open")
def test_evaluate(mock_open, mock_file_open, mock_sleep, mock_console, mock_config, mock_testing_env, mock_requests):
    # Mock file operations
    mock_file = MagicMock()
    mock_file_open.return_value.__enter__.return_value = mock_file
    
    # Run the evaluate function
    evaluate(mock_config)
    
    # Verify testing environment was set up and torn down
    mock_testing_env.setup.assert_called_once()
    mock_testing_env.teardown.assert_called_once()
    
    # Verify requests were made for all payloads
    # Count GET and POST requests
    request_count = mock_requests.get.call_count + mock_requests.post.call_count
    assert request_count >= len(mock_config.attack_payloads) + len(mock_config.traffic_payloads)
    
    # Verify evaded payloads were written to file
    mock_file_open.assert_called_once_with(mock_config.output_evaded_path, "w")
    mock_file.write.assert_called_once_with("payload2\n")


@patch("wafsmith.cmd.evaluate.console")
@patch("wafsmith.cmd.evaluate.time.sleep")
def test_evaluate_error_handling(mock_sleep, mock_console, mock_config, mock_testing_env, mock_requests):
    # Make setup raise an exception
    mock_testing_env.setup.side_effect = Exception("Test error")
    
    # Run the evaluate function
    evaluate(mock_config)
    
    # Verify teardown was still called to clean up
    mock_testing_env.teardown.assert_called_once()