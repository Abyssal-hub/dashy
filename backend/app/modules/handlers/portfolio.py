from typing import Any
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules import ModuleHandler, register
from app.models.portfolio import Asset
from app.db.database import get_db_session


@register("portfolio")
class PortfolioHandler(ModuleHandler):
    """Handler for portfolio/watchlist modules - Now fetches real data from database."""
    
    @property
    def module_type(self) -> str:
        return "portfolio"
    
    async def get_data(self, module_id: str, size: str, db_session: AsyncSession | None = None) -> dict[str, Any]:
        """Return portfolio data with real assets from database."""
        if db_session is None:
            # Fallback: return empty data if no session
            return {
                "module_id": module_id,
                "size": size,
                "assets": [],
                "total_value": 0.0,
                "day_change": 0.0,
                "day_change_percent": 0.0,
            }
        
        result = await db_session.execute(
            select(Asset).where(Asset.module_id == module_id)
        )
        assets = result.scalars().all()
        
        # Calculate totals
        total_value = sum((a.market_value for a in assets), Decimal("0"))
        total_cost = sum((a.cost_basis for a in assets), Decimal("0"))
        day_change = total_value - total_cost
        day_change_percent = 0.0
        if total_cost > 0:
            day_change_percent = float((day_change / total_cost) * 100)
        
        # Build asset list
        asset_list = []
        for asset in assets:
            asset_list.append({
                "id": str(asset.id),
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_type": asset.asset_type,
                "quantity": float(asset.quantity),
                "avg_buy_price": float(asset.avg_buy_price),
                "current_price": float(asset.current_price) if asset.current_price else None,
                "market_value": float(asset.market_value),
                "day_change": float(asset.unrealized_pnl),
                "day_change_percent": asset.unrealized_pnl_percent,
                "currency": asset.currency,
            })
        
        return {
            "module_id": module_id,
            "size": size,
            "assets": asset_list,
            "total_value": float(total_value),
            "day_change": float(day_change),
            "day_change_percent": day_change_percent,
        }
    
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate portfolio config."""
        # MVP: Config is optional, allow empty dict
        return True
