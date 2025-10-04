"""Site configuration with check_updates interface"""

from collections.abc import Callable
from typing import Any, List, Optional, Dict

# Define function types
CheckUpdatesFunc = Callable[[], Dict[str, Any]]
ScheduleFunc = Callable[[], str]
DescriptionFunc = Callable[[], str]
DisplayNameFunc = Callable[[], str]


class SiteConfig:
    """Configuration for a site module with check_updates interface"""

    def __init__(
        self,
        name: str,
        check_updates_func: CheckUpdatesFunc,
        description_func: DescriptionFunc,
        schedule_func: ScheduleFunc,
        display_name_func: DisplayNameFunc = None,
    ):
        # Validate required parameters
        if not name:
            raise ValueError("Site name is required")
        if not check_updates_func or not callable(check_updates_func):
            raise ValueError("check_updates_func must be a callable function")
        if not description_func or not callable(description_func):
            raise ValueError("description_func must be a callable function")
        if not schedule_func or not callable(schedule_func):
            raise ValueError("schedule_func must be a callable function")

        self.check_updates = check_updates_func
        self.description = description_func
        self.schedule = schedule_func
        self.display_name = display_name_func or description_func
        self.name = name