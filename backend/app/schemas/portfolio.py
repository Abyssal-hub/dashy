from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

# Define decimal types with constraints
Decimal20_8 = Annotated[Decimal, Field(ge=0, max_digits=20, decimal_places=8)]
PositiveDecimal = Annotated[Decimal, Field(gt=0, max_digits=20, decimal_places=8)]


class TransactionBase(BaseModel):
    """Base transaction schema."""
    transaction_type: str = Field(..., pattern="^(buy|sell|dividend|split)$")
    quantity: PositiveDecimal
    price: PositiveDecimal
    fees: Decimal20_8 = Field(default=Decimal("0"))
    currency: str = Field(default="USD", min_length=3, max_length=3)
    executed_at: datetime
    notes: str | None = None


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction."""
    pass


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    asset_id: UUID
    total_value: Decimal
    created_at: datetime


class AssetBase(BaseModel):
    """Base asset schema."""
    symbol: str = Field(..., min_length=1, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    asset_type: str = Field(default="stock", pattern="^(stock|crypto|etf|bond|forex|commodity)$")
    currency: str = Field(default="USD", min_length=3, max_length=3)


class AssetCreate(AssetBase):
    """Schema for creating an asset."""
    quantity: Decimal20_8 = Field(default=Decimal("0"))
    avg_buy_price: Decimal20_8 = Field(default=Decimal("0"))


class AssetUpdate(BaseModel):
    """Schema for updating an asset."""
    name: str | None = None
    quantity: Decimal20_8 | None = None
    avg_buy_price: Decimal20_8 | None = None
    current_price: Decimal20_8 | None = None


class AssetResponse(AssetBase):
    """Schema for asset response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    module_id: UUID
    quantity: Decimal
    avg_buy_price: Decimal
    current_price: Decimal | None
    price_updated_at: datetime | None
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: float
    created_at: datetime
    updated_at: datetime


class AssetWithTransactions(AssetResponse):
    """Asset with transaction history."""
    transactions: list[TransactionResponse]


class PortfolioSummary(BaseModel):
    """Portfolio summary statistics."""
    total_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_percent: float
    asset_count: int
    last_updated: datetime | None


class AssetListResponse(BaseModel):
    """Response for listing assets."""
    assets: list[AssetResponse]
    summary: PortfolioSummary
