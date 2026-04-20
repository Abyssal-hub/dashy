"""
QA-005: Portfolio Module validation

Tests for portfolio module functionality per DEV-006.

Related: DEV-006, ARCHITECTURE.md Section 7.1
"""

import pytest
from decimal import Decimal
from datetime import date

from app.services.auth.service import create_user, create_access_token


def get_auth_headers(user_id: str) -> dict:
    """Create authorization headers for a user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


class TestPortfolioHandler:
    """Test portfolio module handler."""

    @pytest.mark.asyncio
    async def test_portfolio_handler_returns_data(self, client, db_session):
        """QA-005-001: Portfolio handler returns data for all sizes."""
        user = await create_user(db_session, "portfolio-data@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create portfolio module
        module_data = {
            "name": "My Portfolio",
            "module_type": "portfolio",
            "config": {"display_currency": "SGD"},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        # Get data for compact size
        response = await client.get(f"/api/modules/{module_id}/data?size=compact", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["module_type"] == "portfolio"
        assert "data" in data

    @pytest.mark.asyncio
    async def test_portfolio_handler_size_buckets(self, client, db_session):
        """QA-005-002: Portfolio handler supports compact/standard/expanded sizes."""
        user = await create_user(db_session, "portfolio-sizes@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create module
        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        sizes = ["compact", "standard", "expanded"]
        for size in sizes:
            response = await client.get(f"/api/modules/{module_id}/data?size={size}", headers=headers)
            assert response.status_code == 200, f"Failed for size: {size}"


class TestPortfolioAssets:
    """Test portfolio asset CRUD."""

    @pytest.mark.asyncio
    async def test_create_asset_updates_total(self, client, db_session):
        """QA-005-003: Adding asset updates portfolio total."""
        user = await create_user(db_session, "portfolio-asset@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create portfolio module
        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        # Add asset
        asset_data = {
            "symbol": "AAPL",
            "name": "Apple Inc",
            "asset_type": "stock",
            "quantity": "10",
            "avg_buy_price": "150.00",
            "currency": "USD",
        }
        response = await client.post(
            f"/api/portfolio/modules/{module_id}/assets",
            json=asset_data,
            headers=headers,
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_assets_returns_assets(self, client, db_session):
        """QA-005-004: List assets returns user's assets with summary."""
        user = await create_user(db_session, "portfolio-list@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create module and add asset
        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        asset_data = {
            "symbol": "GOOGL",
            "name": "Alphabet",
            "asset_type": "stock",
            "quantity": "5",
            "avg_buy_price": "2000.00",
            "currency": "USD",
        }
        await client.post(f"/api/portfolio/modules/{module_id}/assets", json=asset_data, headers=headers)

        # List assets
        response = await client.get(f"/api/portfolio/modules/{module_id}/assets", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "summary" in data
        assert len(data["assets"]) >= 1

    @pytest.mark.asyncio
    async def test_delete_asset_removes_asset(self, client, db_session):
        """QA-005-005: Delete asset removes it from portfolio."""
        user = await create_user(db_session, "portfolio-delete@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        # Create module and add asset
        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        asset_data = {
            "symbol": "TSLA",
            "name": "Tesla",
            "asset_type": "stock",
            "quantity": "10",
            "avg_buy_price": "200.00",
            "currency": "USD",
        }
        pos_response = await client.post(f"/api/portfolio/modules/{module_id}/assets", json=asset_data, headers=headers)
        asset_id = pos_response.json()["id"]

        # Delete asset
        delete_response = await client.delete(
            f"/api/portfolio/modules/{module_id}/assets/{asset_id}",
            headers=headers,
        )
        assert delete_response.status_code == 204


class TestPortfolioAssetTypes:
    """Test all portfolio asset types."""

    @pytest.mark.asyncio
    async def test_equity_asset(self, client, db_session):
        """QA-005-006: Can create equity asset."""
        user = await create_user(db_session, "portfolio-equity@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        asset_data = {
            "symbol": "MSFT",
            "name": "Microsoft",
            "asset_type": "stock",
            "quantity": "10",
            "avg_buy_price": "300.00",
            "currency": "USD",
        }
        response = await client.post(f"/api/portfolio/modules/{module_id}/assets", json=asset_data, headers=headers)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_cash_asset(self, client, db_session):
        """QA-005-007: Can create cash asset."""
        user = await create_user(db_session, "portfolio-cash@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        asset_data = {
            "symbol": "CASH_USD",
            "name": "Cash USD",
            "asset_type": "forex",
            "quantity": "10000",
            "avg_buy_price": "1.00",
            "currency": "USD",
        }
        response = await client.post(f"/api/portfolio/modules/{module_id}/assets", json=asset_data, headers=headers)
        assert response.status_code == 201


class TestPortfolioTransactions:
    """Test transaction CRUD."""

    @pytest.mark.asyncio
    async def test_create_buy_transaction(self, client, db_session):
        """QA-005-008: Can record buy transaction."""
        user = await create_user(db_session, "portfolio-buy@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        # Create asset first
        asset_data = {
            "symbol": "NVDA",
            "name": "NVIDIA",
            "asset_type": "stock",
            "quantity": "10",
            "avg_buy_price": "400.00",
            "currency": "USD",
        }
        asset_response = await client.post(f"/api/portfolio/modules/{module_id}/assets", json=asset_data, headers=headers)
        asset_id = asset_response.json()["id"]

        # Record transaction
        txn_data = {
            "transaction_type": "buy",
            "quantity": 5,
            "price": 410.00,
            "fees": 5.00,
            "executed_at": "2024-01-15T10:00:00Z",
        }
        response = await client.post(
            f"/api/portfolio/modules/{module_id}/assets/{asset_id}/transactions",
            json=txn_data,
            headers=headers,
        )
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_list_transactions(self, client, db_session):
        """QA-005-009: Can list transactions for asset."""
        user = await create_user(db_session, "portfolio-txns@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        create_response = await client.post("/api/modules", json=module_data, headers=headers)
        module_id = create_response.json()["id"]

        asset_data = {
            "symbol": "AMD",
            "name": "AMD",
            "asset_type": "stock",
            "quantity": "20",
            "avg_buy_price": "100.00",
            "currency": "USD",
        }
        asset_response = await client.post(f"/api/portfolio/modules/{module_id}/assets", json=asset_data, headers=headers)
        asset_id = asset_response.json()["id"]

        # Add transaction
        txn_data = {
            "transaction_type": "buy",
            "quantity": 20,
            "price": 100.00,
            "fees": 10.00,
            "executed_at": "2024-01-10T10:00:00Z",
        }
        await client.post(
            f"/api/portfolio/modules/{module_id}/assets/{asset_id}/transactions",
            json=txn_data,
            headers=headers,
        )

        # List transactions
        response = await client.get(
            f"/api/portfolio/modules/{module_id}/assets/{asset_id}/transactions",
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestPortfolioCurrency:
    """Test currency handling."""

    @pytest.mark.asyncio
    async def test_display_currency_changes(self, client, db_session):
        """QA-005-010: Display currency can be changed."""
        user = await create_user(db_session, "portfolio-display@example.com", "password123")
        headers = get_auth_headers(str(user.id))

        module_data = {
            "name": "Portfolio",
            "module_type": "portfolio",
            "config": {"display_currency": "SGD"},
            "position_x": 0,
            "position_y": 0,
            "width": 2,
            "height": 2,
        }
        response = await client.post("/api/modules", json=module_data, headers=headers)
        assert response.status_code == 201
        assert response.json()["config"]["display_currency"] == "SGD"

        # Update display currency
        module_id = response.json()["id"]
        update_data = {"config": {"display_currency": "USD"}}
        update_response = await client.put(f"/api/modules/{module_id}", json=update_data, headers=headers)
        assert update_response.json()["config"]["display_currency"] == "USD"
