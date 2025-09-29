"""
Example site subscription module for testing.
This demonstrates how to create a site subscription module using the functional approach.
"""

import time
from typing import Any
import logging

from ...cache import load_cache
from .. import SiteConfig


async def fetch_example_data():
    """
    Fetch latest content from the source (simulated)
    Returns:
        Latest data from the source
    """
    # Load current update count from cache
    cached_data = load_cache("example")
    current_count = cached_data.get("update_count", 0) if cached_data else 0

    # Simulate fetching data - always increment for testing
    current_time = time.time()
    new_count = current_count + 1

    # Return simulated data
    return {
        "timestamp": current_time,
        "update_count": new_count,
        "title": f"Example Update #{new_count}",
        "content": f"This is example content for update #{new_count}",
    }


def compare_example_data(cached_data: Any, latest_data: Any) -> bool:
    """
    Compare cached data with latest data to determine if there are updates
    Args:
        cached_data: Previously cached data
        latest_data: Latest data fetched from source
    Returns:
        True if there are updates, False otherwise
    """
    # If fetch failed, don't consider it an update
    if latest_data is None:
        return False

    # If no cached data, consider it an update (but only if we have latest_data)
    if cached_data is None:
        return True

    # Compare update counts
    cached_count = cached_data.get("update_count", 0)
    latest_count = latest_data.get("update_count", 0)

    return latest_count > cached_count


def format_example_notification(latest_data: Any) -> str:
    """
    Format the latest data into a notification message
    Args:
        latest_data: Latest data to format
    Returns:
        Formatted notification message
    """
    title = latest_data.get("title", "Unknown Update")
    content = latest_data.get("content", "")
    return f"【示例网站更新】\n{title}\n{content}"


def example_description() -> str:
    """
    Get site description for user display
    Returns:
        Site description
    """
    return "示例网站 - 每10秒更新一次用于测试"


def example_schedule() -> str:
    """
    Get the site's custom fetch schedule (interval format for debugging)
    Returns:
        Interval schedule string (every 10 seconds)
    """
    # Check every 10 seconds for debugging
    return "interval:10"


def example_display_name() -> str:
    """
    Get site display name for user commands
    Returns:
        Site display name
    """
    return "示例网站"


def check_dependencies() -> bool:
    """Check if all dependencies are available"""
    return True


# Register the site using the functional configuration
site = SiteConfig(
    name="example",
    fetch_func=fetch_example_data,
    compare_func=compare_example_data,
    format_func=format_example_notification,
    description_func=example_description,
    schedule_func=example_schedule,
    display_name_func=example_display_name,
)