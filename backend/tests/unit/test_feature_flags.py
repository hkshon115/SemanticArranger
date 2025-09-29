import pytest
from unittest.mock import patch, mock_open
from backend.utils.feature_flags import FeatureFlags

@pytest.fixture
def mock_config_file():
    """Mocks the feature flags YAML file."""
    yaml_content = """
    flag_on:
      enabled: true
      percentage: 100
    
    flag_off:
      enabled: false

    flag_50_percent:
      enabled: true
      percentage: 50
    """
    return mock_open(read_data=yaml_content)

def test_feature_flag_enabled(mock_config_file):
    """Tests a feature flag that is fully enabled."""
    with patch('builtins.open', mock_config_file):
        flags = FeatureFlags()
    assert flags.is_enabled("flag_on") is True

def test_feature_flag_disabled(mock_config_file):
    """Tests a feature flag that is disabled."""
    with patch('builtins.open', mock_config_file):
        flags = FeatureFlags()
    assert flags.is_enabled("flag_off") is False

def test_feature_flag_not_found(mock_config_file):
    """Tests a feature flag that does not exist in the config."""
    with patch('builtins.open', mock_config_file):
        flags = FeatureFlags()
    assert flags.is_enabled("non_existent_flag") is False

def test_percentage_rollout(mock_config_file):
    """
    Tests the percentage-based rollout logic.
    """
    with patch('builtins.open', mock_config_file):
        flags = FeatureFlags()

    # These identifiers are chosen because their MD5 hashes result in
    # scaled values that are inside and outside the 50% threshold.
    identifier_inside = "user-12"  # hash -> ... -> 2
    identifier_outside = "user-13" # hash -> ... -> 67

    assert flags.is_enabled("flag_50_percent", identifier=identifier_inside) is True
    assert flags.is_enabled("flag_50_percent", identifier=identifier_outside) is False

def test_percentage_rollout_no_identifier(mock_config_file):
    """
    Tests that a percentage-based rollout is disabled if no identifier is provided.
    """
    with patch('builtins.open', mock_config_file):
        flags = FeatureFlags()
    assert flags.is_enabled("flag_50_percent") is False
