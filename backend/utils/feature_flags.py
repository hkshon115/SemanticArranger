"""
This module provides a simple feature flag system.

Feature flags allow for turning features on or off without changing the code,
which is useful for A/B testing, gradual rollouts, and managing experimental
features. Flags are defined in a YAML file and can be enabled for a percentage
of users based on a unique identifier.
"""
import yaml
import hashlib
from typing import Dict, Any

class FeatureFlags:
    """
    A simple feature flag system that loads flags from a YAML file.
    """

    def __init__(self, config_path: str = "backend/config/feature_flags.yaml"):
        try:
            with open(config_path, "r") as f:
                self.flags = yaml.safe_load(f)
        except FileNotFoundError:
            self.flags = {}

    def is_enabled(self, flag_name: str, identifier: str = "") -> bool:
        """
        Checks if a feature flag is enabled.

        :param flag_name: The name of the feature flag.
        :param identifier: A unique identifier (e.g., user ID, session ID) for percentage-based rollouts.
        :return: True if the feature is enabled, False otherwise.
        """
        flag_config = self.flags.get(flag_name, {})
        
        if not flag_config.get("enabled", False):
            return False

        percentage = flag_config.get("percentage", 100)
        if percentage >= 100:
            return True

        if not identifier:
            # If no identifier is provided, percentage rollouts are disabled by default
            return False

        # Hash the identifier to get a consistent value
        hashed = hashlib.md5(identifier.encode()).hexdigest()
        # Take the first 4 characters of the hash and convert to an integer
        value = int(hashed[:4], 16)
        
        # Scale the value to be between 0 and 99
        scaled_value = value % 100
        
        return scaled_value < percentage
