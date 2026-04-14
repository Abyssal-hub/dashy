from app.modules.base import ModuleHandler
from app.modules.registry import register, get_handler, list_module_types

# Import handlers to trigger registration
from app.modules.handlers import PortfolioHandler, CalendarHandler, LogHandler

__all__ = ["ModuleHandler", "register", "get_handler", "list_module_types"]
