"""
Template for creating new site subscription modules.
Copy this folder and modify the functions to create a new site module.

Note: If your site module requires additional dependencies, add them to
requirements.txt in your site module directory. Users must manually install
these dependencies before using your site module.

Metadata fields in SiteConfig:
- version: Site module version (default: "1.0.0")
- author: Site module author (default: "Anonymous")
- dependencies: List of required dependencies (default: [])
"""

from typing import Any
# Standard relative imports for plugin directory structure
from ...cache import load_cache
from .. import SiteConfig


async def fetch_data():
    """
    Fetch latest content from the source
    Replace this with actual implementation for your site
    Returns:
        Latest data from the source (can be any JSON-serializable type)
    """
    # TODO: Implement actual data fetching logic
    # Example implementation:
    # import aiohttp
    # async with aiohttp.ClientSession() as session:
    #     async with session.get("https://example.com/api/data") as response:
    #         return await response.json()

    # For now, return None or placeholder data
    return None


def compare_data(cached_data: Any, latest_data: Any) -> bool:
    """
    Compare cached data with latest data to determine if there are updates
    Args:
        cached_data: Previously cached data
        latest_data: Latest data fetched from source
    Returns:
        True if there are updates, False otherwise
    """
    # TODO: Implement comparison logic based on your data structure
    # Example implementation:
    # return cached_data != latest_data

    # For now, always return False (no updates)
    return False


def format_notification(latest_data: Any) -> str:
    """
    Format the latest data into a notification message
    Args:
        latest_data: Latest data to format
    Returns:
        Formatted notification message
    """
    # TODO: Implement formatting logic based on your data structure
    # Example implementation:
    # if latest_data and "title" in latest_data:
    #     return f"网站更新: {latest_data['title']}"

    # For now, return a placeholder message
    return "网站有新更新，请查看!"


def site_description() -> str:
    """
    Get site description for user display
    Returns:
        Site description
    """
    # TODO: Return a description of the site
    return "网站描述"


def site_schedule() -> str:
    """
    Get the site's fetch schedule
    Returns:
        Cron expression or interval string
        Examples:
        - "0 * * * *" (hourly)
        - "0 9 * * *" (daily at 9 AM)
        - "interval:300" (every 5 minutes, for debugging)
    """
    # TODO: Return appropriate schedule
    return "0 * * * *"  # Hourly by default


def site_display_name() -> str:
    """
    Get site display name for user commands
    Returns:
        Site display name
    """
    # TODO: Return user-friendly display name
    return "网站名称"




# Register the site using the functional configuration with metadata
site = SiteConfig(
    name="template",
    fetch_func=fetch_data,
    compare_func=compare_data,
    format_func=format_notification,
    description_func=site_description,
    schedule_func=site_schedule,
    display_name_func=site_display_name,
    version="1.0.0",  # Site module version
    author="Your Name",  # Site module author
    dependencies=[],  # List of required dependencies (e.g., ["httpx", "beautifulsoup4"])
)