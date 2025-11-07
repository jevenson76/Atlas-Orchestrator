"""
API Configuration Management Module

Singleton utility for loading and managing API keys from environment variables
and config files. Supports Anthropic, Google, and OpenAI providers.

Usage:
    from api_config import get_api_key, get_available_providers

    # Get a specific API key
    anthropic_key = get_api_key('anthropic')

    # Check available providers
    providers = get_available_providers()

    # Get detailed status
    status = get_status()
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

# Try to import python-dotenv, but don't fail if not available
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logging.warning("python-dotenv not available. Install with: pip install python-dotenv")

# Configure logging
logger = logging.getLogger(__name__)


class APIConfig:
    """
    Singleton class for managing API keys and configurations.

    Loads API keys from:
    1. Environment variables (primary)
    2. Config file at ~/.claude/config.json (fallback)

    Supported providers: anthropic, google, openai
    """

    _instance = None

    # Environment variable names for each provider
    ENV_VAR_NAMES = {
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'openai': 'OPENAI_API_KEY',
        'xai': 'XAI_API_KEY'
    }

    # Default fallback order (can be customized)
    DEFAULT_FALLBACK_ORDER = ['anthropic', 'xai', 'google', 'openai']

    def __new__(cls):
        """Singleton pattern - only one instance exists."""
        if cls._instance is None:
            cls._instance = super(APIConfig, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize the API configuration."""
        if self._initialized:
            return

        self._api_keys: Dict[str, Optional[str]] = {}
        self._config_file_path = Path.home() / '.claude' / 'config.json'
        self._fallback_order = self.DEFAULT_FALLBACK_ORDER.copy()
        self._key_sources: Dict[str, Optional[str]] = {}  # Track where each key came from

        # Load .env file if dotenv is available
        if DOTENV_AVAILABLE:
            load_dotenv()
            logger.debug("Loaded .env file")

        # Load API keys
        self._load_keys()

        self._initialized = True
        logger.info(f"APIConfig initialized. Available providers: {self.get_available_providers()}")

    def _load_keys(self):
        """Load API keys from environment variables and config file."""
        # First, try environment variables
        for provider, env_var in self.ENV_VAR_NAMES.items():
            key = os.getenv(env_var)
            if key and key.strip():  # Check for non-empty keys
                self._api_keys[provider] = key.strip()
                self._key_sources[provider] = 'environment'
                logger.debug(f"Loaded {provider} API key from environment variable")
            else:
                self._api_keys[provider] = None
                self._key_sources[provider] = None

        # Fall back to config file for missing keys
        if self._config_file_path.exists():
            try:
                with open(self._config_file_path, 'r') as f:
                    config = json.load(f)

                api_keys = config.get('api_keys', {})
                for provider in self.ENV_VAR_NAMES.keys():
                    # Only use config file if environment variable wasn't set
                    if not self._api_keys.get(provider):
                        key = api_keys.get(provider)
                        if key and key.strip():
                            self._api_keys[provider] = key.strip()
                            self._key_sources[provider] = 'config_file'
                            logger.debug(f"Loaded {provider} API key from config file")

                # Load custom fallback order if specified
                if 'fallback_order' in config:
                    custom_order = config['fallback_order']
                    # Validate custom order
                    if isinstance(custom_order, list) and all(p in self.ENV_VAR_NAMES for p in custom_order):
                        self._fallback_order = custom_order
                        logger.debug(f"Loaded custom fallback order: {self._fallback_order}")
                    else:
                        logger.warning(f"Invalid fallback_order in config file, using default")

            except json.JSONDecodeError as e:
                logger.warning(f"Error parsing config file {self._config_file_path}: {e}")
            except Exception as e:
                logger.warning(f"Error reading config file {self._config_file_path}: {e}")
        else:
            logger.debug(f"Config file not found: {self._config_file_path}")

    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.

        Args:
            provider: Provider name ('anthropic', 'google', 'openai')

        Returns:
            API key string or None if not found

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self.ENV_VAR_NAMES:
            raise ValueError(
                f"Unsupported provider: '{provider}'. "
                f"Supported providers: {list(self.ENV_VAR_NAMES.keys())}"
            )

        key = self._api_keys.get(provider)

        if not key:
            logger.warning(
                f"No API key found for '{provider}'. "
                f"Set {self.ENV_VAR_NAMES[provider]} environment variable "
                f"or add to {self._config_file_path}"
            )

        return key

    def get_available_providers(self) -> List[str]:
        """
        Get list of providers with valid API keys.

        Returns:
            List of provider names that have API keys configured
        """
        return [provider for provider, key in self._api_keys.items() if key]

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed status of all API configurations.

        Returns:
            Dictionary with status information for each provider:
            {
                'anthropic': {
                    'configured': True,
                    'source': 'environment' or 'config_file',
                    'key_preview': 'sk-ant-...xyz',
                    'env_var': 'ANTHROPIC_API_KEY'
                },
                ...
            }
        """
        status = {}

        for provider in self.ENV_VAR_NAMES.keys():
            key = self._api_keys.get(provider)

            if key:
                # Get source
                source = self._key_sources.get(provider, 'unknown')

                # Create preview (first 10 and last 3 chars)
                if len(key) > 13:
                    preview = f"{key[:10]}...{key[-3:]}"
                else:
                    preview = key[:3] + "***" if len(key) > 3 else "***"

                status[provider] = {
                    'configured': True,
                    'source': source,
                    'key_preview': preview,
                    'env_var': self.ENV_VAR_NAMES[provider]
                }
            else:
                status[provider] = {
                    'configured': False,
                    'source': None,
                    'key_preview': None,
                    'env_var': self.ENV_VAR_NAMES[provider]
                }

        return status

    def get_fallback_order(self) -> List[str]:
        """
        Get provider fallback order.

        Returns:
            List of provider names in fallback order
        """
        return self._fallback_order.copy()

    def set_fallback_order(self, order: List[str]):
        """
        Set custom provider fallback order.

        Args:
            order: List of provider names in desired order

        Raises:
            ValueError: If order contains invalid providers
        """
        # Validate all providers
        for provider in order:
            if provider not in self.ENV_VAR_NAMES:
                raise ValueError(
                    f"Invalid provider in fallback order: '{provider}'. "
                    f"Valid providers: {list(self.ENV_VAR_NAMES.keys())}"
                )

        self._fallback_order = order.copy()
        logger.info(f"Updated fallback order: {self._fallback_order}")

    def has_any_key(self) -> bool:
        """
        Check if at least one API key is configured.

        Returns:
            True if any provider has an API key
        """
        return len(self.get_available_providers()) > 0

    def get_first_available_provider(self) -> Optional[str]:
        """
        Get the first available provider according to fallback order.

        Returns:
            Provider name or None if no providers available
        """
        for provider in self._fallback_order:
            if self._api_keys.get(provider):
                return provider
        return None

    def reload(self):
        """
        Reload API keys from environment and config file.
        Useful if environment variables or config file changed.
        """
        logger.info("Reloading API configuration...")
        self._api_keys.clear()
        self._key_sources.clear()
        self._fallback_order = self.DEFAULT_FALLBACK_ORDER.copy()

        if DOTENV_AVAILABLE:
            load_dotenv(override=True)

        self._load_keys()
        logger.info(f"Reload complete. Available providers: {self.get_available_providers()}")


# Convenience functions for easy import
def get_api_key(provider: str) -> Optional[str]:
    """
    Get API key for a provider (convenience function).

    Args:
        provider: Provider name ('anthropic', 'google', 'openai')

    Returns:
        API key string or None if not found
    """
    return APIConfig().get_api_key(provider)


def get_available_providers() -> List[str]:
    """
    Get list of available providers (convenience function).

    Returns:
        List of provider names with configured API keys
    """
    return APIConfig().get_available_providers()


def get_status() -> Dict[str, Dict[str, Any]]:
    """
    Get detailed status (convenience function).

    Returns:
        Dictionary with configuration status for all providers
    """
    return APIConfig().get_status()


def get_fallback_order() -> List[str]:
    """
    Get provider fallback order (convenience function).

    Returns:
        List of provider names in fallback order
    """
    return APIConfig().get_fallback_order()


# Example usage and testing
if __name__ == "__main__":
    # Set logging to INFO for demo
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s',
        force=True
    )

    config = APIConfig()

    print("\n" + "="*50)
    print("API Configuration Status")
    print("="*50 + "\n")

    # Show status for all providers
    status = config.get_status()
    for provider, info in status.items():
        print(f"{provider.upper()}:")
        if info['configured']:
            print(f"  ✓ Configured (source: {info['source']})")
            print(f"  Preview: {info['key_preview']}")
        else:
            print(f"  ✗ Not configured")
            print(f"  Set {info['env_var']} or add to config file")
        print()

    # Show available providers
    available = config.get_available_providers()
    print(f"Available providers: {', '.join(available) if available else 'None'}")
    print()

    # Show fallback order
    print(f"Fallback order: {' → '.join(config.get_fallback_order())}")
    print()

    # Show first available
    first = config.get_first_available_provider()
    if first:
        print(f"First available provider: {first}")
    else:
        print("⚠ No providers available - please configure API keys")

    print("\n" + "="*50)
    print(f"Config file location: {config._config_file_path}")
    print("="*50 + "\n")

    # Show example config file format
    if not config.has_any_key():
        print("Example config file format (~/.claude/config.json):")
        print(json.dumps({
            "api_keys": {
                "anthropic": "your-anthropic-key-here",
                "google": "your-google-key-here",
                "openai": "your-openai-key-here"
            },
            "fallback_order": ["anthropic", "google", "openai"]
        }, indent=2))
        print()
