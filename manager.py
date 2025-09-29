import json
import os
from pathlib import Path

from astrbot.api import logger


class SubscriptionManager:
    """Manage user/group subscriptions to websites"""

    def __init__(self):
        """Initialize subscription manager"""
        # Use AstrBot's data directory for storing subscription data
        self.data_file = Path("data/astrbot_plugin_stonk/subscriptions.json")
        self.session_file = Path("data/astrbot_plugin_stonk/sessions.json")
        # New structure: {site_name: {"users": [user_ids], "groups": [group_ids]}}
        self.subscriptions: dict[str, dict[str, list[str]]] = {}
        # Store session context for notification sending: {subscriber_id: unified_msg_origin}
        # This now includes both users and groups
        self.subscriber_sessions: dict[str, str] = {}

    def initialize(self):
        """Initialize subscription manager"""
        self.load_subscriptions()
        logger.info("订阅管理器初始化完成")

    def load_subscriptions(self):
        """Load subscriptions from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, encoding="utf-8") as f:
                    self.subscriptions = json.load(f)
                # Count total subscriptions for logging
                total_subs = sum(
                    len(site_data.get("users", [])) + len(site_data.get("groups", []))
                    for site_data in self.subscriptions.values()
                )
                logger.info(f"已加载 {len(self.subscriptions)} 个站点，共 {total_subs} 个订阅")
            else:
                self.subscriptions = {}
                self.save_subscriptions()
                logger.info("创建新的订阅数据文件")
        except Exception as e:
            logger.error(f"加载订阅数据失败: {e}")
            self.subscriptions = {}

        # Load session data
        try:
            if self.session_file.exists():
                with open(self.session_file, encoding="utf-8") as f:
                    self.subscriber_sessions = json.load(f)
                logger.info(f"已加载 {len(self.subscriber_sessions)} 个会话数据")
            else:
                self.subscriber_sessions = {}
                self.save_sessions()
                logger.info("创建新的会话数据文件")
        except Exception as e:
            logger.error(f"加载会话数据失败: {e}")
            self.subscriber_sessions = {}

    def save_subscriptions(self):
        """Save subscriptions to file"""
        try:
            # Ensure directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
            logger.debug("订阅数据已保存")
        except Exception as e:
            logger.error(f"保存订阅数据失败: {e}")

    def save_sessions(self):
        """Save session data to file"""
        try:
            # Ensure directory exists
            self.session_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(self.subscriber_sessions, f, ensure_ascii=False, indent=2)
            logger.debug("会话数据已保存")
        except Exception as e:
            logger.error(f"保存会话数据失败: {e}")

    def subscribe(self, user_id: str, site_name: str, is_group: bool = False, session_context: str = None) -> bool:
        """
        Subscribe user/group to a site
        Args:
            user_id: User or group ID
            site_name: Site name to subscribe to
            is_group: Whether the ID is a group ID (True) or user ID (False)
            session_context: Unified message origin for notification sending
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle special "全部" site
            if site_name == "全部":
                site_name = "all"

            # Initialize site in subscriptions if it doesn't exist
            if site_name not in self.subscriptions:
                self.subscriptions[site_name] = {"users": [], "groups": []}

            # Determine target list based on whether it's a group or user
            target_list = "groups" if is_group else "users"

            # Check if already subscribed
            if user_id in self.subscriptions[site_name][target_list]:
                target_type = "群组" if is_group else "用户"
                site_display_name = "全部" if site_name == "all" else site_name
                logger.info(f"{target_type} {user_id} 已经订阅了 {site_display_name}")
                return False

            # Add subscription
            self.subscriptions[site_name][target_list].append(user_id)

            # Store session context for notification sending (for both users and groups)
            if session_context:
                self.subscriber_sessions[user_id] = session_context
                self.save_sessions()

            self.save_subscriptions()
            target_type = "群组" if is_group else "用户"
            site_display_name = "全部" if site_name == "all" else site_name
            logger.info(f"{target_type} {user_id} 订阅了 {site_display_name}")
            return True
        except Exception as e:
            logger.error(f"订阅失败: {e}")
            return False

    def unsubscribe(self, user_id: str, site_name: str, is_group: bool = False) -> bool:
        """
        Unsubscribe user/group from a site
        Args:
            user_id: User or group ID
            site_name: Site name to unsubscribe from
            is_group: Whether the ID is a group ID (True) or user ID (False)
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle special "全部" site
            if site_name == "全部":
                site_name = "all"

            # Check if site exists and user/group is subscribed
            if site_name in self.subscriptions:
                target_list = "groups" if is_group else "users"
                if user_id in self.subscriptions[site_name][target_list]:
                    self.subscriptions[site_name][target_list].remove(user_id)

                    # Clean up empty site entries (but don't clean up "all" site)
                    if (
                        site_name != "all"
                        and not self.subscriptions[site_name]["users"]
                        and not self.subscriptions[site_name]["groups"]
                    ):
                        del self.subscriptions[site_name]

                    self.save_subscriptions()
                    target_type = "群组" if is_group else "用户"
                    site_display_name = "全部" if site_name == "all" else site_name
                    logger.info(f"{target_type} {user_id} 取消订阅了 {site_display_name}")
                    return True

            target_type = "群组" if is_group else "用户"
            site_display_name = "全部" if site_name == "all" else site_name
            logger.info(f"{target_type} {user_id} 未订阅 {site_display_name}")
            return False
        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return False

    def get_subscriptions(self, user_id: str, is_group: bool = False) -> list[str]:
        """
        Get user/group subscriptions
        Args:
            user_id: User or group ID
            is_group: Whether the ID is a group ID (True) or user ID (False)
        Returns:
            List of subscribed site names
        """
        subscriptions = []
        target_list = "groups" if is_group else "users"

        for site_name, site_data in self.subscriptions.items():
            if user_id in site_data.get(target_list, []):
                # Convert "all" back to "全部" for display
                if site_name == "all":
                    subscriptions.append("全部")
                else:
                    subscriptions.append(site_name)

        return subscriptions

    def get_subscribers(self, site_name: str) -> list[str]:
        """
        Get all subscribers for a site
        Args:
            site_name: Site name
        Returns:
            List of user/group IDs subscribed to the site
        """
        subscribers = []

        # Add subscribers for the specific site
        if site_name in self.subscriptions:
            site_data = self.subscriptions[site_name]
            # Add all users
            subscribers.extend(site_data.get("users", []))
            # Add all groups
            subscribers.extend(site_data.get("groups", []))

        # Add subscribers who subscribed to "全部" (all sites)
        if "all" in self.subscriptions:
            all_data = self.subscriptions["all"]
            # Add all users who subscribed to all
            subscribers.extend(all_data.get("users", []))
            # Add all groups who subscribed to all
            subscribers.extend(all_data.get("groups", []))

        return subscribers

    def get_all_subscriptions(self) -> dict[str, dict[str, list[str]]]:
        """
        Get all subscriptions
        Returns:
            Dictionary of all subscriptions with site as first level keys
        """
        return self.subscriptions


# Create global subscription manager instance
subscription_manager = SubscriptionManager()