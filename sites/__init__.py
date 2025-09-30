"""Functional approach to site modules - minimal fetch/compare/format functions"""

from collections.abc import Callable
from typing import Any, List, Optional

# Define function types
FetchFunc = Callable[[], Any]
CompareFunc = Callable[[Any, Any], bool]
FormatFunc = Callable[[Any], str]
ScheduleFunc = Callable[[], str]
DescriptionFunc = Callable[[], str]
DisplayNameFunc = Callable[[], str]


class SiteConfig:
    """Configuration for a site module with functional components and metadata"""

    def __init__(
        self,
        name: str,
        fetch_func: FetchFunc,
        compare_func: CompareFunc,
        format_func: FormatFunc,
        description_func: DescriptionFunc,
        schedule_func: ScheduleFunc,
        display_name_func: DisplayNameFunc = None,
        version: str = "1.0.0",
        dependencies: List[str] = None,
        author: str = "Anonymous",
    ):
        # Validate required parameters
        if not name:
            raise ValueError("Site name is required")
        if not fetch_func or not callable(fetch_func):
            raise ValueError("fetch_func must be a callable function")
        if not compare_func or not callable(compare_func):
            raise ValueError("compare_func must be a callable function")
        if not format_func or not callable(format_func):
            raise ValueError("format_func must be a callable function")
        if not description_func or not callable(description_func):
            raise ValueError("description_func must be a callable function")
        if not schedule_func or not callable(schedule_func):
            raise ValueError("schedule_func must be a callable function")

        self.name = name
        self.fetch = fetch_func
        self.compare = compare_func
        self.format = format_func
        self.description = description_func
        self.schedule = schedule_func
        self.display_name = display_name_func or description_func
        self.version = version
        self.dependencies = dependencies or []
        self.author = author