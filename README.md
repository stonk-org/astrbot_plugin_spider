# AstrBot Stonk Plugin

网站订阅插件，可以订阅不同网站的更新并推送给用户。

## 功能

- 订阅网站更新
- 自动检测网站内容变化
- 推送更新通知给订阅用户
- 支持多种网站模块扩展

## 使用方法

### 订阅命令

- `/订阅 <网站名>` - 订阅指定网站
- `/取消订阅 <网站名>` - 取消订阅指定网站
- `/订阅列表` - 查看可订阅的网站列表
- `/订阅全部` - 订阅所有网站
- `/取消订阅全部` - 取消订阅所有网站

### 示例

```
/订阅列表
/订阅 示例网站
/取消订阅 示例网站
```

## 网站模块开发

插件支持通过创建网站模块来扩展支持的网站类型。所有网站模块都使用标准化的目录结构。

### 标准模块结构

所有网站模块都遵循相同的目录结构：

```
sites/
├── example/
│   ├── __init__.py
│   ├── requirements.txt
│   └── main.py
└── template/
    ├── __init__.py
    ├── requirements.txt
    └── main.py
```

每个网站模块都是一个独立的目录，包含：
- `__init__.py`: 空的初始化文件
- `requirements.txt`: 该模块的特定依赖（如果没有额外依赖，可以留空）
- `main.py`: 主模块文件，包含所有必要的函数

### 模块文件结构

主模块文件包含以下必要函数：

```python
# sites/example/main.py
from typing import Any
from ...cache import load_cache
from .. import SiteConfig

async def fetch_data():
    """获取网站最新数据"""
    pass

def compare_data(cached_data: Any, latest_data: Any) -> bool:
    """比较缓存数据和最新数据"""
    pass

def format_notification(latest_data: Any) -> str:
    """格式化通知消息"""
    pass

def site_description() -> str:
    """网站描述"""
    pass

def site_schedule() -> str:
    """检查频率设置"""
    pass

def site_display_name() -> str:
    """显示名称"""
    pass

def check_dependencies() -> bool:
    """检查依赖是否可用"""
    return True

# 注册网站配置
site = SiteConfig(
    name="site_name",
    fetch_func=fetch_data,
    compare_func=compare_data,
    format_func=format_notification,
    description_func=site_description,
    schedule_func=site_schedule,
    display_name_func=site_display_name,
)
```

### 依赖管理

在 `requirements.txt` 中声明特定依赖：

```txt
# example/requirements.txt (无额外依赖)
# 所有需要的包都由 AstrBot 核心提供
```

```txt
# 其他模块的 requirements.txt 示例
requests>=2.28.0
beautifulsoup4>=4.12.0
```

在模块中检查依赖：

```python
# sites/my_site/my_site.py
try:
    import requests
    import bs4
    DEPENDENCIES_AVAILABLE = True
except ImportError as e:
    DEPENDENCIES_AVAILABLE = False
    logging.warning(f"依赖导入失败: {e}")

async def fetch_data():
    """获取网站最新数据"""
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError("缺少依赖，请运行: pip install requests beautifulsoup4")
    # 实现获取数据逻辑

def check_dependencies() -> bool:
    """检查依赖是否可用"""
    return DEPENDENCIES_AVAILABLE
```

### 开发步骤

1. 复制 `sites/template/` 目录并重命名为你的网站名称
2. 修改目录内的文件名和内容
3. 在 `requirements.txt` 中声明任何特定依赖
4. 实现所有必要的函数
5. 重启 AstrBot 使新模块生效

## 配置

插件数据存储在 AstrBot 的 `data` 目录下：
- 订阅信息：`data/astrbot_plugin_stonk/subscriptions.json`
- 会话信息：`data/astrbot_plugin_stonk/sessions.json`
- 网站缓存：`data/astrbot_plugin_stonk/cache/`

## 注意事项

- 插件停用时会自动取消所有后台任务
- 启用插件后会自动开始检查网站更新
