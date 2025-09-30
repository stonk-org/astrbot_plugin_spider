"""Cache management module for site data"""

import json
from pathlib import Path
from typing import Any
from astrbot.core.star.star_tools import StarTools


def get_cache_dir():
    """Get the cache directory using StarTools.get_data_dir"""
    return StarTools.get_data_dir("astrbot_plugin_stonk") / "cache"


def get_cache_file(site_name: str) -> Path:
    """Get cache file path for a site"""
    cache_dir = get_cache_dir()
    return cache_dir / f"{site_name}_subscription.json"


def load_cache(site_name: str) -> Any:
    """Load cached data for a site

    Args:
        site_name: Name of the site

    Returns:
        Cached data or None if not found
    """
    cache_file = get_cache_file(site_name)
    try:
        if cache_file.exists():
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        # Log the error but don't fail - return None to indicate no cache
        from astrbot.api import logger
        logger.warning(f"Failed to load cache for site {site_name}: {e}")
    return None


def save_cache(site_name: str, data: Any) -> bool:
    """Save data to cache for a site

    Args:
        site_name: Name of the site
        data: Data to cache

    Returns:
        True if successful, False otherwise
    """
    cache_file = get_cache_file(site_name)
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        # Log the error
        from astrbot.api import logger
        logger.error(f"Failed to save cache for site {site_name}: {e}")
        return False