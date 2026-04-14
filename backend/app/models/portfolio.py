import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Numeric, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base

if TYPE_CHECKING:
    from app.models.module import Module


class Asset(Base):
    """Asset in a portfolio module."""
    
    __tablename__ = "portfolio_assets"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Asset details
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(20), nullable=False, default="stock")
    # stock, crypto, etf, bond, forex, commodity
    
    # Position
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    avg_buy_price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    
    # Current price (updated by background job)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 8), nullable=True)
    price_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # Relationships
    module = relationship("Module", back_populates="assets")
    transactions = relationship("Transaction", back_populates="asset", cascade="all, delete-orphan")
    
    @property
    def market_value(self) -> Decimal:
        """Calculate current market value."""
        if self.current_price:
            return self.quantity * self.current_price
        return Decimal("0")
    
    @property
    def cost_basis(self) -> Decimal:
        """Calculate total cost basis."""
        return self.quantity * self.avg_buy_price
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized profit/loss."""
        return self.market_value - self.cost_basis
    
    @property
    def unrealized_pnl_percent(self) -> float:
        """Calculate unrealized P&L percentage."""
        if self.cost_basis and self.cost_basis > 0:
            return float((self.unrealized_pnl / self.cost_basis) * 100)
        return 0.0
    
    def __repr__(self) -> str:
        return f"<Asset(symbol={self.symbol}, qty={self.quantity})>"


class Transaction(Base):
    """Transaction record for an asset."""
    
    __tablename__ = "portfolio_transactions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_assets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Transaction details
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # buy, sell, dividend, split
    
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    fees: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    
    # Timestamp
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Metadata
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    
    # Relationships
    asset = relationship("Asset", back_populates="transactions")
    
    @property
    def total_value(self) -> Decimal:
        """Total value of transaction (including fees)."""
        return (self.quantity * self.price) + self.fees
    
    def __repr__(self) -> str:
        return f"<Transaction(type={self.transaction_type}, symbol={self.asset.symbol if self.asset else None})>"
