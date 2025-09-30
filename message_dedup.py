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
        self.sent_messages: Dict[str, float] = {}  # {message_hash: timestamp}
        self.load_sent_messages()

    def load_sent_messages(self):
        """Load sent messages from file"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Filter out messages older than 7 days
                    current_time = time.time()
                    seven_days_ago = current_time - (7 * 24 * 60 * 60)  # 7 days in seconds

                    self.sent_messages = {
                        msg_hash: timestamp
                        for msg_hash, timestamp in data.items()
                        if timestamp > seven_days_ago
                    }

                    logger.info(f"已加载 {len(self.sent_messages)} 条近期发送的消息记录")
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

    def is_duplicate(self, message: str) -> bool:
        """Check if message is a duplicate sent within 7 days"""
        message_hash = self._hash_message(message)
        current_time = time.time()

        # Check if message exists in our records
        if message_hash in self.sent_messages:
            # Check if it was sent within the last 7 days
            seven_days_ago = current_time - (7 * 24 * 60 * 60)
            if self.sent_messages[message_hash] > seven_days_ago:
                return True

        return False

    def record_message(self, message: str):
        """Record that a message has been sent"""
        message_hash = self._hash_message(message)
        self.sent_messages[message_hash] = time.time()
        self.save_sent_messages()

    def cleanup_old_records(self):
        """Remove records older than 7 days"""
        current_time = time.time()
        seven_days_ago = current_time - (7 * 24 * 60 * 60)

        old_count = len(self.sent_messages)
        self.sent_messages = {
            msg_hash: timestamp
            for msg_hash, timestamp in self.sent_messages.items()
            if timestamp > seven_days_ago
        }

        new_count = len(self.sent_messages)
        if old_count != new_count:
            logger.info(f"清理了 {old_count - new_count} 条过期消息记录")
            self.save_sent_messages()


# Global instance
message_dedup = MessageDeduplication()