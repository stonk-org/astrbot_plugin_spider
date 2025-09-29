import importlib
import asyncio
from pathlib import Path
from typing import Any

from astrbot.api import logger
from astrbot.api.message_components import Plain

from .cache import load_cache, save_cache
from .manager import subscription_manager
from .sites import SiteConfig


class Scheduler:
    def __init__(self):
        """初始化 Scheduler 类
        - 管理网站订阅检查任务
        """
        self.site_configs: dict[str, SiteConfig] = {}  # {site_name: site_config}
        self.display_name_to_site_name: dict[str, str] = {}  # {display_name: site_name}
        self.tasks = {}  # {site_name: task}
        self.context = None  # Will be set by the plugin

    def load_site_modules(self):
        """Load all site subscription modules using functional approach"""
        sites_dir = Path(__file__).parent / "sites"
        loaded_sites = []

        # Load all site directories (standardized structure)
        for dir_path in sites_dir.iterdir():
            if dir_path.is_dir() and dir_path.name not in ["__pycache__", "template"]:
                site_name = dir_path.name
                if not self._load_site_module(site_name, is_directory=True):
                    continue

                loaded_sites.append(site_name)

        # Add "全部" to display name mapping
        self.display_name_to_site_name["全部"] = "all"

        logger.info(f"已加载 {len(loaded_sites)} 个站点模块: {', '.join(loaded_sites) if loaded_sites else '无'}")
        return loaded_sites

    def _load_site_module(self, site_name: str, is_directory: bool = False) -> bool:
        """Load a single site module"""
        try:
            if is_directory:
                # Check for site-specific requirements
                self._check_site_requirements(site_name)

                # Import from directory
                module = importlib.import_module(f".sites.{site_name}.main", package=__package__)
            else:
                # Import the site module using relative import
                module = importlib.import_module(f".sites.{site_name}", package=__package__)

            logger.debug(f"成功导入站点模块: {site_name}")

            # Look for the 'site' attribute which should be a SiteConfig
            if hasattr(module, "site") and isinstance(module.site, SiteConfig):
                # Register with scheduler
                self.site_configs[site_name] = module.site

                # Map display name to site name
                display_name = module.site.display_name()
                self.display_name_to_site_name[display_name] = site_name

                # Start scheduling for this site
                self.start_site_scheduling(site_name)

                logger.info(f"成功加载站点模块: {site_name} (显示名称: {display_name})")
                return True
            else:
                logger.warning(f"站点模块 {site_name} 中未找到有效的 SiteConfig")
                return False

        except ImportError as e:
            logger.error(f"加载站点模块 {site_name} 失败，缺少依赖: {e}")
            logger.info(f"请检查站点 {site_name} 的依赖要求")
            return False
        except Exception as e:
            logger.error(f"加载站点模块 {site_name} 失败: {e}")
            return False

    def _check_site_requirements(self, site_name: str):
        """Check and warn about site-specific requirements"""
        sites_dir = Path(__file__).parent / "sites"
        requirements_file = sites_dir / site_name / "requirements.txt"

        if requirements_file.exists():
            logger.info(f"站点 {site_name} 有特定依赖要求，请查看 {requirements_file} 文件")
            # In a more advanced implementation, we could parse and validate dependencies here

    def start_site_scheduling(self, site_name: str):
        """
        Start scheduling for a specific site
        Args:
            site_name: Name of the site to schedule
        """
        if site_name not in self.site_configs:
            logger.error(f"站点 {site_name} 未注册")
            return

        site_config = self.site_configs[site_name]
        try:
            # Get schedule from site
            schedule = site_config.schedule()

            # Check if schedule is a special debug interval (starts with "interval:")
            if schedule.startswith("interval:"):
                # Parse interval (e.g., "interval:10" for 10 seconds)
                interval_seconds = int(schedule.split(":")[1])

                # Create and start asyncio task for interval checking
                async def site_check_task():
                    while True:
                        try:
                            await self.check_site_updates(site_name)
                        except Exception as e:
                            logger.error(f"检查站点 {site_name} 更新时出错: {e}")
                        await asyncio.sleep(interval_seconds)

                # Start the task
                task = asyncio.create_task(site_check_task())
                self.tasks[site_name] = task

                logger.info(f"已为站点 {site_name} 启动调试任务: 每 {interval_seconds} 秒")
            else:
                # Parse cron expression (for now, we'll just use a simplified version)
                cron_parts = schedule.split()
                if len(cron_parts) != 5:
                    logger.error(f"站点 {site_name} 的调度表达式格式错误: {schedule}")
                    return

                # For simplicity, we'll convert cron to interval (in minutes)
                # In a production version, you'd want to use a proper cron parser
                minute, hour, day, month, day_of_week = cron_parts

                # Simple conversion for demonstration - use minute field as interval in minutes
                try:
                    interval_minutes = int(minute) if minute.isdigit() else 60  # default to hourly
                except:
                    interval_minutes = 60  # default to hourly

                # Create and start asyncio task for interval checking
                async def site_check_task():
                    while True:
                        try:
                            await self.check_site_updates(site_name)
                        except Exception as e:
                            logger.error(f"检查站点 {site_name} 更新时出错: {e}")
                        await asyncio.sleep(interval_minutes * 60)  # Convert to seconds

                # Start the task
                task = asyncio.create_task(site_check_task())
                self.tasks[site_name] = task

                logger.info(f"已为站点 {site_name} 启动定时任务: 每 {interval_minutes} 分钟")
        except Exception as e:
            logger.error(f"为站点 {site_name} 启动定时任务失败: {e}")

    async def check_site_updates(self, site_name: str):
        """
        Check for updates from a specific site using functional approach
        Args:
            site_name: Name of the site to check
        """
        if site_name not in self.site_configs:
            logger.error(f"站点 {site_name} 未注册")
            return

        site_config = self.site_configs[site_name]
        try:
            logger.debug(f"开始检查站点 {site_name} 的更新")

            # Load cached data using cache module
            cached_data = load_cache(site_name)

            # Fetch latest data using site's fetch function
            latest_data = await site_config.fetch()

            # Check for updates using site's compare function
            if site_config.compare(cached_data, latest_data):
                logger.info(f"站点 {site_name} 检测到更新")

                # Format notification using site's format function
                notification = site_config.format(latest_data)

                # Get subscribers
                subscribers = subscription_manager.get_subscribers(site_name)

                # Send notifications to all subscribers
                if subscribers:
                    await self._send_notifications(subscribers, notification)
                else:
                    logger.debug(f"站点 {site_name} 没有订阅者")

                # Save new data to cache using cache module
                save_cache(site_name, latest_data)
            else:
                logger.debug(f"站点 {site_name} 无更新")

        except Exception as e:
            logger.error(f"检查站点 {site_name} 更新时出错: {e}")

    async def _send_notifications(self, subscribers: list[str], message: str):
        """
        Send notifications to subscribers
        Args:
            subscribers: List of subscriber IDs (user IDs or group IDs)
            message: Notification message
        """
        try:
            if not self.context:
                logger.error("Context not available for sending notifications")
                return

            # Import message components
            from astrbot.api.message_components import Plain
            from astrbot.api.event import MessageChain

            for subscriber_id in subscribers:
                try:
                    # Check if we have stored session context for this subscriber
                    if subscriber_id in subscription_manager.subscriber_sessions:
                        # Send to stored session context
                        unified_msg_origin = subscription_manager.subscriber_sessions[subscriber_id]
                        # Validate session context before sending
                        if unified_msg_origin:
                            message_chain = MessageChain().message(message)
                            await self.context.send_message(unified_msg_origin, message_chain)
                            logger.info(f"已向订阅者 {subscriber_id} 发送通知")
                        else:
                            logger.warning(f"订阅者 {subscriber_id} 的会话上下文无效")
                    else:
                        # For subscribers without stored context,
                        # we cannot send messages as we don't have the required session information
                        # This happens when:
                        # 1. User or group has not subscribed yet
                        # 2. Session data was corrupted or missing
                        logger.info(f"订阅者 {subscriber_id} 没有会话上下文，将无法接收通知。请订阅以接收更新。")

                except Exception as e:
                    logger.error(f"向订阅者 {subscriber_id} 发送通知失败: {e}")
                    # Continue with other subscribers even if one fails
                    continue
        except Exception as e:
            logger.error(f"发送通知时出错: {e}")

    def get_site_name_by_display_name(self, display_name: str) -> str:
        """Get internal site name by display name"""
        return self.display_name_to_site_name.get(display_name, display_name)

    def cancel_all_tasks(self):
        """
        Cancel all running scheduler tasks
        """
        try:
            for site_name, task in self.tasks.items():
                if not task.done():
                    task.cancel()
                    logger.info(f"已取消站点 {site_name} 的定时任务")
            self.tasks.clear()
            logger.info("所有定时任务已取消")
        except Exception as e:
            logger.error(f"取消定时任务时出错: {e}")


# 创建 Scheduler 实例
scheduler_instance = Scheduler()