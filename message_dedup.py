"""Message deduplication system to prevent sending duplicate messages within 7 days"""

import json
import time
from pathlib import Path
from typing import Dict, Any
from astrbot.api import logger

from .manager import get_data_dir


class MessageDeduplication:
    """Deduplication system for preventing duplicate message sending"""

    def __init__(self):
        """Initialize message deduplication system"""
        self.data_file = get_data_dir() / "sent_messages.json"
        self.sent_messages: Dict[str, Dict[str, float]] = {}  # {site: {message_hash: timestamp}}
        self.load_sent_messages()

    def load_sent_messages(self):
        """Load sent messages from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    current_time = time.time()
                    seven_days_ago = current_time - (7 * 24 * 60 * 60)  # 7 days in seconds

                    # New format: {site: {message_hash: timestamp}}
                    self.sent_messages = {}
                    total_messages = 0
                    for site, site_data in data.items():
                        if isinstance(site_data, dict):
                            cleaned_site_data = {
                                msg_hash: timestamp
                                for msg_hash, timestamp in site_data.items()
                                if timestamp > seven_days_ago
                            }
                            if cleaned_site_data:
                                self.sent_messages[site] = cleaned_site_data
                                total_messages += len(cleaned_site_data)

                    logger.info(f"已加载 {total_messages} 条近期发送的消息记录（按站点分组）")
                    self.save_sent_messages()  # Save cleaned data
            else:
                self.sent_messages = {}
                logger.info("创建新的消息记录文件")
        except Exception as e:
            logger.error(f"加载消息记录失败: {e}")
            self.sent_messages = {}

    def save_sent_messages(self):
        """Save sent messages to file"""
        try:
            # Ensure directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.sent_messages, f, ensure_ascii=False, indent=2)
            logger.debug("消息记录已保存")
        except Exception as e:
            logger.error(f"保存消息记录失败: {e}")

    def _hash_message(self, message: str) -> str:
        """Create a hash of the message content"""
        import hashlib
        return hashlib.md5(message.encode('utf-8')).hexdigest()

    def is_duplicate(self, message: str, site: str = "default") -> bool:
        """Check if message is a duplicate sent within 7 days for the specified site"""
        message_hash = self._hash_message(message)
        current_time = time.time()
        seven_days_ago = current_time - (7 * 24 * 60 * 60)

        # Check if site exists in our records
        if site in self.sent_messages:
            # Clean up old records for this site on-the-fly
            site_data = self.sent_messages[site]
            # Remove old records and check for duplicate in one pass
            still_valid = {}
            is_dup = False

            for msg_hash, timestamp in site_data.items():
                if timestamp > seven_days_ago:
                    still_valid[msg_hash] = timestamp
                    if msg_hash == message_hash:
                        is_dup = True

            self.sent_messages[site] = still_valid
            return is_dup

        return False

    def record_message(self, message: str, site: str = "default"):
        """Record that a message has been sent for the specified site"""
        message_hash = self._hash_message(message)
        current_time = time.time()
        seven_days_ago = current_time - (7 * 24 * 60 * 60)

        # Ensure site exists in our records
        if site not in self.sent_messages:
            self.sent_messages[site] = {}

        # Clean up old records for this site before adding new one
        site_data = self.sent_messages[site]
        still_valid = {
            msg_hash: timestamp
            for msg_hash, timestamp in site_data.items()
            if timestamp > seven_days_ago
        }
        still_valid[message_hash] = current_time
        self.sent_messages[site] = still_valid

        self.save_sent_messages()


# Global instance
message_dedup = MessageDeduplication()