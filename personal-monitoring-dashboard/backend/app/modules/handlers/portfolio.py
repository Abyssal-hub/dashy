from typing import Any

from app.modules import ModuleHandler, register


@register("portfolio")
class PortfolioHandler(ModuleHandler):
    """Handler for portfolio/watchlist modules."""
    
    @property
    def module_type(self) -> str:
        return "portfolio"
    
    async def get_data(self, module_id: str, size: str) -> dict[str, Any]:
        """Return portfolio data (placeholder implementation)."""
        return {
            "module_id": module_id,
            "size": size,
            "assets": [],
            "total_value": 0.0,
            "day_change": 0.0,
            "day_change_percent": 0.0,
        }
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate portfolio config has required fields."""
        required = ["symbols"]
        return all(field in config for field in required)
