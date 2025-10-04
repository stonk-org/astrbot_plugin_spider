import importlib
import asyncio
from pathlib import Path
from typing import Any

from astrbot.api import logger
from astrbot.api.message_components import Plain
from astrbot.core.star.star_tools import StarTools

# APScheduler imports
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .manager import subscription_manager, get_data_dir
from .sites import SiteConfig


class Scheduler:
    def __init__(self):
        """初始化 Scheduler 类
        - 管理网站订阅检查任务
        """
        self.site_configs: dict[str, SiteConfig] = {}  # {site_name: site_config}
        self.display_name_to_site_name: dict[str, str] = {}  # {display_name: site_name}
        self.context = None  # Will be set by the plugin
        self.plugin_instance = None  # Will be set by the plugin

        # Initialize APScheduler
        self.scheduler = AsyncIOScheduler()
        self.scheduler_jobs = {}  # {site_name: job_id}

        # Start the scheduler
        self.scheduler.start()

    def get_config_value(self, key, default=None):
        """Get configuration value with default fallback"""
        if self.plugin_instance and hasattr(self.plugin_instance, 'get_config_value'):
            return self.plugin_instance.get_config_value(key, default)
        return default

    def load_site_modules(self):
        """Load all site subscription modules from both plugin and custom directories"""
        sites_dir = Path(__file__).parent / "sites"
        custom_sites_dir = get_data_dir() / "sites"

        loaded_sites = []
        loaded_site_names = set()  # Track loaded site names to avoid duplicates

        # Load site directories from plugin directory (standardized structure)
        logger.info(f"正在从插件目录加载站点模块: {sites_dir}")
        for dir_path in sites_dir.iterdir():
            if dir_path.is_dir() and dir_path.name not in ["__pycache__", "template"] and not dir_path.name.startswith('.'):
                site_name = dir_path.name
                # Skip if site with same name already loaded
                if site_name in loaded_site_names:
                    logger.warning(f"跳过重复站点模块: {site_name} (自定义版本已加载)")
                    continue

                if not self._load_site_module(site_name, is_directory=True, base_path=sites_dir):
                    continue

                loaded_sites.append(site_name)
                loaded_site_names.add(site_name)

        # Load site directories from custom directory (user-defined structure)
        if custom_sites_dir.exists():
            logger.info(f"正在从自定义目录加载站点模块: {custom_sites_dir}")
            for dir_path in custom_sites_dir.iterdir():
                if dir_path.is_dir() and dir_path.name not in ["__pycache__", "template"] and not dir_path.name.startswith('.'):
                    site_name = dir_path.name
                    # Warn if site with same name already loaded
                    if site_name in loaded_site_names:
                        logger.warning(f"覆盖插件站点模块: {site_name} (使用自定义版本)")
                        # Remove the previously loaded site
                        if site_name in self.site_configs:
                            del self.site_configs[site_name]

                    if not self._load_site_module(site_name, is_directory=True, base_path=custom_sites_dir):
                        continue

                    # Update loaded sites list - replace if exists, otherwise append
                    if site_name not in loaded_sites:
                        loaded_sites.append(site_name)
                    loaded_site_names.add(site_name)
        else:
            logger.info(f"自定义站点目录不存在，将创建: {custom_sites_dir}")
            try:
                custom_sites_dir.mkdir(parents=True, exist_ok=True)
                logger.info(f"已创建自定义站点目录: {custom_sites_dir}")
            except Exception as e:
                logger.warning(f"创建自定义站点目录失败: {e}")


        logger.info(f"已加载 {len(loaded_sites)} 个站点模块: {', '.join(loaded_sites) if loaded_sites else '无'}")
        return loaded_sites

    def _load_site_module(self, site_name: str, is_directory: bool = False, base_path: Path = None) -> bool:
        """Load a single site module from specified base path"""
        import importlib.util
        import sys

        try:
            if base_path is None:
                # Default to plugin sites directory
                base_path = Path(__file__).parent / "sites"

            # Determine if we're loading from plugin directory or custom directory
            is_plugin_dir = base_path == Path(__file__).parent / "sites"

            if is_directory:
                if is_plugin_dir:
                    # Import from plugin directory using relative import
                    module = importlib.import_module(f".sites.{site_name}.main", package=__package__)
                else:
                    # Import from custom directory using spec loading with plugin path
                    # Add plugin parent directory to sys.path so custom sites can import plugin modules
                    plugin_parent_dir = str(Path(__file__).parent.parent)
                    plugin_dir_name = Path(__file__).parent.name
                    added_to_path = False
                    if plugin_parent_dir not in sys.path:
                        sys.path.insert(0, plugin_parent_dir)
                        added_to_path = True

                    try:
                        custom_site_path = base_path / site_name

                        # Try to import main module directly
                        main_py = custom_site_path / "main.py"
                        if not main_py.exists():
                            logger.error(f"自定义站点模块 {site_name} 缺少 main.py 文件")
                            return False

                        spec = importlib.util.spec_from_file_location(f"custom_sites.{site_name}.main", main_py)
                        module = importlib.util.module_from_spec(spec)
                        # Add to sys.modules before executing to support relative imports
                        sys.modules[spec.name] = module
                        logger.debug(f"执行站点模块 {site_name} 的代码")
                        spec.loader.exec_module(module)
                        logger.debug(f"站点模块 {site_name} 执行完成")
                    finally:
                        # Remove plugin parent directory from sys.path if we added it
                        if added_to_path and plugin_parent_dir in sys.path:
                            sys.path.remove(plugin_parent_dir)
            else:
                if is_plugin_dir:
                    # Import the site module using relative import
                    module = importlib.import_module(f".sites.{site_name}", package=__package__)
                else:
                    logger.error(f"不支持从自定义目录加载非目录形式的站点模块: {site_name}")
                    return False

            logger.debug(f"成功导入站点模块: {site_name} (来自: {base_path})")

            # Look for the 'site' attribute which should be a SiteConfig
            if hasattr(module, "site"):
                site_obj = module.site
                # Check if it's a SiteConfig-like object by checking for required attributes
                # New SiteConfig has: name, check_updates, description, schedule, display_name
                required_attrs = ['name', 'check_updates', 'description', 'schedule', 'display_name']
                is_site_config = all(hasattr(site_obj, attr) for attr in required_attrs)

                if is_site_config:
                    # Register with scheduler
                    self.site_configs[site_name] = site_obj

                    # Map display name to site name
                    display_name = site_obj.display_name()
                    self.display_name_to_site_name[display_name] = site_name

                    # Start scheduling for this site
                    self.start_site_scheduling(site_name)

                    source_type = "插件" if is_plugin_dir else "自定义"
                    logger.info(f"成功加载{source_type}站点模块: {site_name} (显示名称: {display_name})")
                    return True
                else:
                    logger.warning(f"站点模块 {site_name} 中的 site 变量不是有效的 SiteConfig 类型: {type(site_obj)}")
                    # Log missing attributes for debugging
                    missing_attrs = [attr for attr in required_attrs if not hasattr(site_obj, attr)]
                    logger.debug(f"站点模块 {site_name} 中 site 对象缺少属性: {missing_attrs}")
                    return False
            else:
                logger.warning(f"站点模块 {site_name} 中未找到 site 变量")
                # Log module attributes for debugging
                logger.debug(f"站点模块 {site_name} 的属性: {dir(module)}")
                return False

        except ImportError as e:
            logger.error(f"加载站点模块 {site_name} 失败，缺少依赖: {e}")
            logger.info(f"请检查站点 {site_name} 的依赖要求")
            return False
        except Exception as e:
            logger.error(f"加载站点模块 {site_name} 失败: {e}")
            return False


    def start_site_scheduling(self, site_name: str):
        """
        Start scheduling for a specific site using APScheduler
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

            # Remove any existing job for this site
            if site_name in self.scheduler_jobs:
                job_id = self.scheduler_jobs[site_name]
                self.scheduler.remove_job(job_id)
                logger.debug(f"已移除站点 {site_name} 的旧任务")

            # Check if schedule is a special debug interval (starts with "interval:")
            if schedule.startswith("interval:"):
                # Parse interval (e.g., "interval:10" for 10 seconds)
                try:
                    interval_seconds = int(schedule.split(":")[1])

                    # Create interval trigger
                    trigger = IntervalTrigger(seconds=interval_seconds)

                    # Add job to scheduler
                    job = self.scheduler.add_job(
                        self.check_site_updates,
                        trigger,
                        args=[site_name],
                        id=f"site_{site_name}_interval",
                        name=f"站点 {site_name} 间隔任务 ({interval_seconds} 秒)"
                    )

                    # Store job ID
                    self.scheduler_jobs[site_name] = job.id

                    logger.info(f"已为站点 {site_name} 启动间隔任务: 每 {interval_seconds} 秒")
                except (ValueError, IndexError) as e:
                    logger.error(f"站点 {site_name} 的间隔格式错误: {schedule}")
                    return
            else:
                # Parse cron expression
                cron_parts = schedule.split()
                if len(cron_parts) != 5:
                    logger.error(f"站点 {site_name} 的调度表达式格式错误: {schedule}")
                    return

                try:
                    # Parse cron parts: minute, hour, day, month, day_of_week
                    minute, hour, day, month, day_of_week = cron_parts

                    # Create cron trigger (APScheduler handles * and other cron syntax properly)
                    trigger = CronTrigger(
                        minute=minute,
                        hour=hour,
                        day=day,
                        month=month,
                        day_of_week=day_of_week
                    )

                    # Add job to scheduler
                    job = self.scheduler.add_job(
                        self.check_site_updates,
                        trigger,
                        args=[site_name],
                        id=f"site_{site_name}_cron",
                        name=f"站点 {site_name} 定时任务 ({schedule})"
                    )

                    # Store job ID
                    self.scheduler_jobs[site_name] = job.id

                    logger.info(f"已为站点 {site_name} 启动定时任务: {schedule}")
                except Exception as e:
                    logger.error(f"为站点 {site_name} 创建定时任务失败: {e}")
                    return

        except Exception as e:
            logger.error(f"为站点 {site_name} 启动定时任务失败: {e}")

    async def check_site_updates(self, site_name: str):
        """
        Check for updates from a specific site using the new check_updates approach
        that handles caching and returns multiple messages.
        Args:
            site_name: Name of the site to check
        """
        if site_name not in self.site_configs:
            logger.error(f"站点 {site_name} 未注册")
            return

        # Check if anyone is subscribed to this site before running it
        subscribers = subscription_manager.get_subscribers(site_name)
        if not subscribers:
            logger.debug(f"站点 {site_name} 没有订阅者，跳过检查更新")
            return

        site_config = self.site_configs[site_name]
        try:
            logger.debug(f"开始检查站点 {site_name} 的更新")

            # New interface: site handles everything including caching
            result = await site_config.check_updates()

            # Handle the result
            if not result or not isinstance(result, dict):
                logger.error(f"站点 {site_name} 返回无效的结果格式")
                return

            success = result.get('success', False)
            error = result.get('error', '')
            messages = result.get('messages', [])

            if not success:
                logger.error(f"站点 {site_name} 检查更新失败: {error}")
                return

            if not messages:
                logger.debug(f"站点 {site_name} 无新内容，跳过发送通知")
                return

            # Process each message
            for message in messages:
                if not message:
                    continue

                # Send notifications to all subscribers (we already checked they exist)
                await self._send_notifications(subscribers, message)

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

            # Get batch size from configuration
            batch_size = self.get_config_value('notification_batch_size', 50)

            # Process subscribers in batches to avoid overload
            for i in range(0, len(subscribers), batch_size):
                batch = subscribers[i:i + batch_size]

                # Import message components
                from astrbot.api.message_components import Plain
                from astrbot.api.event import MessageChain

                for subscriber_id in batch:
                    try:
                        # Check if we have stored session context for this subscriber
                        if subscriber_id in subscription_manager.subscriber_sessions:
                            # Send to stored session context
                            unified_msg_origin = subscription_manager.subscriber_sessions[subscriber_id]
                            # Validate session context before sending
                            if unified_msg_origin:
                                message_chain = MessageChain().message(message)
                                await StarTools.send_message(unified_msg_origin, message_chain)
                                logger.debug(f"通知内容: {message}")
                                logger.info(f"已向订阅者 {subscriber_id} 发送通知")
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
        Cancel all running scheduler tasks and shutdown APScheduler
        """
        try:
            # Remove all scheduled jobs
            job_count = len(self.scheduler_jobs)
            if job_count > 0:
                for site_name, job_id in self.scheduler_jobs.items():
                    try:
                        self.scheduler.remove_job(job_id)
                        logger.info(f"已移除站点 {site_name} 的调度任务")
                    except Exception as e:
                        logger.warning(f"移除站点 {site_name} 的调度任务失败: {e}")

                self.scheduler_jobs.clear()
                logger.info(f"已移除 {job_count} 个调度任务")

            # Shutdown the scheduler
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("调度器已关闭")

        except Exception as e:
            logger.error(f"取消定时任务时出错: {e}")


# 创建 Scheduler 实例
scheduler_instance = Scheduler()