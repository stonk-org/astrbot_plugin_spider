from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .manager import subscription_manager
from .scheduler import scheduler_instance

@register("stonk", "zanderzhng", "网站订阅插件，可以订阅不同网站的更新并推送给用户", "1.0.0", "https://github.com/zanderzhng/astrbot-plugin-stonk")
class StonkPlugin(Star):
    """Website subscription plugin for AstrBot"""

    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("网站订阅插件正在初始化...")

        # Set context for scheduler
        scheduler_instance.context = context

        # Initialize subscription manager
        try:
            subscription_manager.initialize()
            logger.info("订阅管理器初始化完成")
        except Exception as e:
            logger.error(f"订阅管理器初始化失败: {e}")

        # Load site modules
        try:
            loaded_sites = scheduler_instance.load_site_modules()
            logger.info(f"网站订阅模块加载完成，共加载 {len(loaded_sites)} 个站点")
        except Exception as e:
            logger.error(f"网站订阅模块加载失败: {e}")

        logger.info("网站订阅插件初始化完成")

    async def terminate(self):
        """Plugin cleanup when unloaded"""
        logger.info("网站订阅插件正在关闭...")
        # Cancel all scheduler tasks
        scheduler_instance.cancel_all_tasks()
        logger.info("网站订阅插件已关闭")

    # Subscription command handlers
    @filter.command("订阅")
    async def handle_subscribe(self, event: AstrMessageEvent, site_name: str = ""):
        """处理订阅命令"""
        if not site_name:
            yield event.plain_result("请指定要订阅的网站名称")
            return

        # 获取用户/群组ID
        is_group = event.message_obj.group_id != ""
        if is_group:
            target_id = event.get_group_id()
            target_type = "群组"
        else:
            target_id = event.get_sender_id()
            target_type = "用户"

        # Convert display name to internal site name
        internal_site_name = scheduler_instance.get_site_name_by_display_name(site_name)

        # 订阅站点
        session_context = event.unified_msg_origin
        success = subscription_manager.subscribe(target_id, internal_site_name, is_group, session_context)

        if success:
            yield event.plain_result(f"{target_type} {target_id} 已订阅 {site_name}")
        else:
            yield event.plain_result(f"{target_type} {target_id} 订阅 {site_name} 失败")

    @filter.command("取消订阅")
    async def handle_unsubscribe(self, event: AstrMessageEvent, site_name: str = ""):
        """处理取消订阅命令"""
        if not site_name:
            yield event.plain_result("请指定要取消订阅的网站名称")
            return

        # 获取用户/群组ID
        is_group = event.message_obj.group_id != ""
        if is_group:
            target_id = event.get_group_id()
            target_type = "群组"
        else:
            target_id = event.get_sender_id()
            target_type = "用户"

        # Convert display name to internal site name
        internal_site_name = scheduler_instance.get_site_name_by_display_name(site_name)

        # 取消订阅站点
        success = subscription_manager.unsubscribe(target_id, internal_site_name, is_group)

        if success:
            yield event.plain_result(f"{target_type} {target_id} 已取消订阅 {site_name}")
        else:
            yield event.plain_result(f"{target_type} {target_id} 未订阅 {site_name} 或取消订阅失败")

    @filter.command("订阅列表")
    async def handle_list_subscriptions(self, event: AstrMessageEvent):
        """处理列出订阅命令"""
        # 获取用户/群组ID
        is_group = event.message_obj.group_id != ""
        if is_group:
            target_id = event.get_group_id()
        else:
            target_id = event.get_sender_id()

        # 获取用户的订阅
        user_subscriptions = subscription_manager.get_subscriptions(target_id, is_group)

        # 获取所有可用的站点
        available_sites = list(scheduler_instance.site_configs.keys())

        # 创建消息
        if not available_sites:
            message = "暂无可用的订阅源"
        else:
            message = "订阅列表:\n"

            # 显示已订阅的站点
            if user_subscriptions:
                message += "已订阅:\n"
                for site in user_subscriptions:
                    if site == "全部":
                        message += f"✓ {site} - 接收所有站点的通知\n"
                    elif site in scheduler_instance.site_configs:
                        display_name = scheduler_instance.site_configs[site].display_name()
                        description = scheduler_instance.site_configs[site].description()
                        message += f"✓ {display_name} - {description}\n"
                    else:
                        message += f"✓ {site} - (描述不可用)\n"
                message += "\n"

            # 显示未订阅的站点
            unsubscribed_sites = [site for site in available_sites if site not in user_subscriptions and site != "all"]
            # Add "全部" to unsubscribed list if not subscribed
            if "全部" not in user_subscriptions:
                unsubscribed_sites.append("全部")

            if unsubscribed_sites:
                message += "未订阅:\n"
                for site in unsubscribed_sites:
                    if site == "全部":
                        message += f"○ {site} - 接收所有站点的通知\n"
                    elif site in scheduler_instance.site_configs:
                        display_name = scheduler_instance.site_configs[site].display_name()
                        description = scheduler_instance.site_configs[site].description()
                        message += f"○ {display_name} - {description}\n"
                    else:
                        message += f"○ {site} - (描述不可用)\n"

        yield event.plain_result(message)

    @filter.command("订阅全部")
    async def handle_subscribe_all(self, event: AstrMessageEvent):
        """处理订阅全部命令"""
        # 获取用户/群组ID
        is_group = event.message_obj.group_id != ""
        if is_group:
            target_id = event.get_group_id()
            target_type = "群组"
        else:
            target_id = event.get_sender_id()
            target_type = "用户"

        # 订阅全部站点
        session_context = event.unified_msg_origin
        success = subscription_manager.subscribe(target_id, "全部", is_group, session_context)

        if success:
            yield event.plain_result(f"{target_type} {target_id} 已订阅全部站点")
        else:
            yield event.plain_result(f"{target_type} {target_id} 订阅全部站点失败")

    @filter.command("取消订阅全部")
    async def handle_unsubscribe_all(self, event: AstrMessageEvent):
        """处理取消订阅全部命令"""
        # 获取用户/群组ID
        is_group = event.message_obj.group_id != ""
        if is_group:
            target_id = event.get_group_id()
            target_type = "群组"
        else:
            target_id = event.get_sender_id()
            target_type = "用户"

        # 取消订阅全部站点
        success = subscription_manager.unsubscribe(target_id, "全部", is_group)

        if success:
            yield event.plain_result(f"{target_type} {target_id} 已取消订阅全部站点")
        else:
            yield event.plain_result(f"{target_type} {target_id} 未订阅全部站点或取消订阅失败")
