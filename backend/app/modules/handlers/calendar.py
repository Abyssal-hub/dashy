from typing import Any

from app.modules import ModuleHandler, register


@register("calendar")
class CalendarHandler(ModuleHandler):
    """Handler for economic calendar modules."""
    
    @property
    def module_type(self) -> str:
        return "calendar"
    
    async def get_data(self, module_id: str, size: str) -> dict[str, Any]:
        """Return calendar events (placeholder implementation)."""
        return {
            "module_id": module_id,
            "size": size,
            "events": [],
            "date_range": {"start": None, "end": None},
        }
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate calendar config has required fields."""
        required = ["currencies", "impact_levels"]
        return all(field in config for field in required)
