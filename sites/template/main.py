"""
Template for creating new site subscription modules.
Copy this folder and modify the check_updates function to create a new site module.

Note: If your site module requires additional dependencies, add them to
requirements.txt in your site module directory. Users must manually install
these dependencies before using your site module.

The check_updates function handles everything:
- Fetching data from the source
- Loading/saving cache data (using the provided cache utilities)
- Comparing with previous data to find updates
- Formatting multiple notification messages
- Returning structured results

Metadata fields in SiteConfig:
- version: Site module version (default: "1.0.0")
- author: Site module author (default: "Anonymous")
- dependencies: List of required dependencies (default: [])
"""

from typing import Any, Dict, List

# Standard relative imports for plugin directory structure
from ...cache import load_cache, save_cache
from .. import SiteConfig


async def check_updates() -> Dict[str, Any]:
    """
    Check for updates and return structured result with multiple messages.
    This function handles everything: fetching, caching, diffing, and formatting.

    Returns:
        Dict with keys:
        - success: bool (True if check completed successfully)
        - error: str (error message if success=False)
        - messages: List[str] (list of notification messages, can be empty)
    """
    try:
        # Load cached data
        site_name = "template"
        cached_data = load_cache(site_name)

        # Fetch latest data from source
        latest_data = await fetch_data()

        if latest_data is None:
            return {
                "success": False,
                "error": "Failed to fetch data from source",
                "messages": []
            }

        # Compare with cached data to find updates
        messages = []
        if cached_data is None:
            # First run - treat all data as new
            messages = format_multiple_notifications(latest_data)
        else:
            # Find differences between cached and latest data
            new_items = find_new_items(cached_data, latest_data)
            if new_items:
                messages = format_multiple_notifications(new_items)

        # Save latest data to cache
        save_cache(site_name, latest_data)

        return {
            "success": True,
            "error": "",
            "messages": messages
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "messages": []
        }


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


def find_new_items(cached_data: Any, latest_data: Any) -> List[Any]:
    """
    Find new items in latest_data that are not in cached_data
    Args:
        cached_data: Previously cached data
        latest_data: Latest data fetched from source
    Returns:
        List of new items that should be notified
    """
    # TODO: Implement logic to find new items based on your data structure
    # Example for list of items with unique IDs:
    # cached_ids = {item['id'] for item in cached_data.get('items', [])}
    # new_items = [item for item in latest_data.get('items', []) if item['id'] not in cached_ids]
    # return new_items

    # For now, return empty list
    return []


def format_multiple_notifications(data: Any) -> List[str]:
    """
    Format data into multiple notification messages
    Args:
        data: Data to format (could be single item or list of items)
    Returns:
        List of formatted notification messages
    """
    # TODO: Implement formatting logic based on your data structure
    # Example implementation:
    # if isinstance(data, list):
    #     return [f"网站更新: {item['title']}" for item in data]
    # else:
    #     return [f"网站更新: {data['title']}"]

    # For now, return a single placeholder message
    return ["网站有新更新，请查看!"]


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


# Register the site using the check_updates interface
site = SiteConfig(
    name="template",
    check_updates_func=check_updates,
    description_func=site_description,
    schedule_func=site_schedule,
    display_name_func=site_display_name,
    version="1.0.0",  # Site module version
    author="Your Name",  # Site module author
    dependencies=[],  # List of required dependencies (e.g., ["httpx", "beautifulsoup4"])
)