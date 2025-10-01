"""
Example site subscription module for testing.
This demonstrates how to create a site subscription module using the check_updates interface.
The example simulates multiple updates per check cycle to demonstrate multi-message support.
"""

import time
from typing import Any, Dict, List

# Standard relative imports for plugin directory structure
from ...cache import load_cache, save_cache
from .. import SiteConfig

# Get logger from astrbot
from astrbot.api import logger


async def check_example_updates() -> Dict[str, Any]:
    """
    Check for updates and return structured result with multiple messages.
    This example simulates multiple updates per check cycle to demonstrate
    multi-message capability with proper caching.

    Returns:
        Dict with keys:
        - success: bool (True if check completed successfully)
        - error: str (error message if success=False)
        - messages: List[str] (list of notification messages, can be empty)
    """
    try:
        site_name = "example"

        # Load cached data
        cached_data = load_cache(site_name)

        # Get current update count from cache or start from 0
        last_update_count = cached_data.get("update_count", 0) if cached_data else 0

        # Simulate new update count (increment by 1-3 to simulate multiple updates)
        import time
        current_time = int(time.time())
        new_update_count = last_update_count + 1

        # Generate 1-3 new messages for this update cycle
        import random
        num_messages = random.randint(1, 3)
        messages = []
        for i in range(1, num_messages + 1):
            update_num = new_update_count + i - 1
            messages.append(
                f"【示例网站更新】\nExample Update #{update_num}\nThis is example content {i}"
            )

        # Prepare data to save to cache
        latest_data = {
            "timestamp": current_time,
            "update_count": new_update_count + len(messages) - 1,
            "title": f"Example Update #{new_update_count + len(messages) - 1}",
            "content": f"This is example content for update #{new_update_count + len(messages) - 1}"
        }

        # Save latest data to cache
        save_cache(site_name, latest_data)

        logger.info(f"示例网站返回 {len(messages)} 条新消息 (更新计数: {new_update_count})")
        return {
            "success": True,
            "error": "",
            "messages": messages
        }

    except Exception as e:
        logger.error(f"示例网站检查更新时出错: {e}")
        return {
            "success": False,
            "error": str(e),
            "messages": []
        }


def example_description() -> str:
    """
    Get site description for user display
    Returns:
        Site description
    """
    return "示例网站 - 每10秒更新一次用于测试（支持多消息）"


def example_schedule() -> str:
    """
    Get the site's custom fetch schedule
    Returns:
        Cron schedule string (every 5 minutes)
    """
    # Check every 5 minutes
    return "* * * * *"

def example_display_name() -> str:
    """
    Get site display name for user commands
    Returns:
        Site display name
    """
    return "示例网站"


# Register the site using the check_updates interface
site = SiteConfig(
    name="example",
    check_updates_func=check_example_updates,
    description_func=example_description,
    schedule_func=example_schedule,
    display_name_func=example_display_name,
)