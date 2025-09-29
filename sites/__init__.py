"""Functional approach to site modules - minimal fetch/compare/format functions"""

from collections.abc import Callable
from typing import Any

# Define function types
FetchFunc = Callable[[], Any]
CompareFunc = Callable[[Any, Any], bool]
FormatFunc = Callable[[Any], str]
ScheduleFunc = Callable[[], str]
DescriptionFunc = Callable[[], str]
DisplayNameFunc = Callable[[], str]


class SiteConfig:
    """Configuration for a site module with functional components"""

    def __init__(
        self,
        name: str,
        fetch_func: FetchFunc,
        compare_func: CompareFunc,
        format_func: FormatFunc,
        description_func: DescriptionFunc,
        schedule_func: ScheduleFunc,
        display_name_func: DisplayNameFunc = None,
    ):
        self.name = name
        self.fetch = fetch_func
        self.compare = compare_func
        self.format = format_func
        self.description = description_func
        self.schedule = schedule_func
        self.display_name = display_name_func or description_func