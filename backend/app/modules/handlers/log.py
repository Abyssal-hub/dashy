from typing import Any

from app.modules import ModuleHandler, register


@register("log")
class LogHandler(ModuleHandler):
    """Handler for system log modules."""
    
    @property
    def module_type(self) -> str:
        return "log"
    
    async def get_data(self, module_id: str, size: str) -> dict[str, Any]:
        """Return system logs (placeholder implementation)."""
        return {
            "module_id": module_id,
            "size": size,
            "logs": [],
            "severities": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        }
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate log config."""
        # MVP: Config is optional, allow empty dict
        return True
