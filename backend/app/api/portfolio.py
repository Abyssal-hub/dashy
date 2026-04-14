from typing import Any
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.services.auth.deps import get_current_user
from app.db.database import get_db_session
from app.models.module import Module
from app.models.portfolio import Asset, Transaction
from app.schemas.portfolio import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    AssetWithTransactions,
    AssetListResponse,
    TransactionCreate,
    TransactionResponse,
    PortfolioSummary,
)

router = APIRouter(prefix="/portfolio", tags=["portfolio"])


async def _get_module_and_verify(
    db: AsyncSession,
    module_id: str,
    user_id: str,
) -> Module:
    """Get module and verify ownership and type."""
    result = await db.execute(
        select(Module).where(
            Module.id == module_id,
            Module.user_id == user_id,
            Module.module_type == "portfolio",
        )
    )
    module = result.scalar_one_or_none()
    
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio module not found",
        )
    
    return module


async def _calculate_portfolio_summary(
    db: AsyncSession,
    module_id: str,
) -> PortfolioSummary:
    """Calculate portfolio summary statistics."""
    result = await db.execute(
        select(Asset).where(Asset.module_id == module_id)
    )
    assets = result.scalars().all()
    
    total_value = sum((a.market_value for a in assets), Decimal("0"))
    total_cost = sum((a.cost_basis for a in assets), Decimal("0"))
    pnl = total_value - total_cost
    
    pnl_percent = 0.0
    if total_cost > 0:
        pnl_percent = float((pnl / total_cost) * 100)
    
    # Get last price update
    last_updates = [a.price_updated_at for a in assets if a.price_updated_at]
    last_updated = max(last_updates) if last_updates else None
    
    return PortfolioSummary(
        total_value=total_value,
        total_cost_basis=total_cost,
        total_unrealized_pnl=pnl,
        total_unrealized_pnl_percent=pnl_percent,
        asset_count=len(assets),
        last_updated=last_updated,
    )


@router.get("/modules/{module_id}/assets", response_model=AssetListResponse)
async def list_assets(
    module_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """List all assets in a portfolio module."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    result = await db.execute(
        select(Asset).where(Asset.module_id == module_id)
    )
    assets = result.scalars().all()
    
    summary = await _calculate_portfolio_summary(db, module_id)
    
    return AssetListResponse(
        assets=assets,
        summary=summary,
    )


@router.post("/modules/{module_id}/assets", response_model=AssetResponse, status_code=201)
async def create_asset(
    module_id: str,
    asset_data: AssetCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Add a new asset to the portfolio."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    # Check if symbol already exists in this module
    result = await db.execute(
        select(Asset).where(
            Asset.module_id == module_id,
            Asset.symbol == asset_data.symbol,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Asset {asset_data.symbol} already exists in this portfolio",
        )
    
    asset = Asset(
        module_id=module_id,
        **asset_data.model_dump(),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    
    return asset


@router.get("/modules/{module_id}/assets/{asset_id}", response_model=AssetWithTransactions)
async def get_asset(
    module_id: str,
    asset_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Get asset details with transaction history."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.module_id == module_id,
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    
    return asset


@router.put("/modules/{module_id}/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    module_id: str,
    asset_id: str,
    asset_data: AssetUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Update asset details."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.module_id == module_id,
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    
    update_data = asset_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(asset, field, value)
    
    await db.commit()
    await db.refresh(asset)
    
    return asset


@router.delete("/modules/{module_id}/assets/{asset_id}", status_code=204)
async def delete_asset(
    module_id: str,
    asset_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> None:
    """Remove an asset from the portfolio."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.module_id == module_id,
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    
    await db.delete(asset)
    await db.commit()


@router.post("/modules/{module_id}/assets/{asset_id}/transactions", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    module_id: str,
    asset_id: str,
    transaction_data: TransactionCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """Record a transaction for an asset."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.module_id == module_id,
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    
    transaction = Transaction(
        asset_id=asset_id,
        **transaction_data.model_dump(),
    )
    
    # Update asset position based on transaction type
    if transaction_data.transaction_type == "buy":
        # Calculate new average buy price
        total_cost = (asset.quantity * asset.avg_buy_price) + (transaction_data.quantity * transaction_data.price) + transaction_data.fees
        total_qty = asset.quantity + transaction_data.quantity
        if total_qty > 0:
            asset.avg_buy_price = total_cost / total_qty
        asset.quantity = total_qty
        
    elif transaction_data.transaction_type == "sell":
        if transaction_data.quantity > asset.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot sell more than owned quantity",
            )
        asset.quantity -= transaction_data.quantity
    
    db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    
    return transaction


@router.get("/modules/{module_id}/assets/{asset_id}/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    module_id: str,
    asset_id: str,
    db: AsyncSession = Depends(get_db_session),
    current_user_id: str = Depends(get_current_user),
) -> Any:
    """List all transactions for an asset."""
    await _get_module_and_verify(db, module_id, current_user_id)
    
    result = await db.execute(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.module_id == module_id,
        )
    )
    asset = result.scalar_one_or_none()
    
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asset not found",
        )
    
    result = await db.execute(
        select(Transaction).where(Transaction.asset_id == asset_id)
        .order_by(Transaction.executed_at.desc())
    )
    
    return result.scalars().all()
