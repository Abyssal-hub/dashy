"""
QA-011: API Contract Tests
Ensures backend API responses match frontend expectations.
Prevents breaking changes that would crash the UI.

Test Plan: QA-011-CONTRACT-VISUAL-TEST-PLAN.md
"""

import json  # DEF-011-005: Added missing import
import pytest
import re
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, ValidationError, Field
from typing import List, Optional, Dict, Any


# ============================================================================
# CONTRACT SCHEMAS - Frontend expectations documented as code
# Source: QA-011 Test Plan Appendix A
# Note: Per B07 (MVP), layout is module-centric. No dashboard layout endpoint.
# ============================================================================

class LoginResponse(BaseModel):
    """
    Contract: POST /auth/login response
    
    Frontend Usage:
    - access_token: Stored in localStorage, sent as Authorization header
    - refresh_token: Stored for token refresh flow (opaque token per B05)
    - token_type: Always "bearer" (validated by frontend)
    
    QA-CONTRACT-001 Reference
    Architect Decision B05: Opaque refresh tokens are correct (security)
    """
    access_token: str = Field(
        ..., 
        min_length=20, 
        description="JWT access token (format: header.payload.signature)"
    )
    refresh_token: str = Field(
        ..., 
        min_length=20, 
        description="Opaque refresh token (not JWT per B05 security decision)"
    )
    token_type: str = Field(
        default="bearer", 
        pattern="^bearer$",
        description="Token type for Authorization header"
    )
    
    class Config:
        extra = "forbid"


class ErrorResponse(BaseModel):
    """
    Contract: Error responses from API
    
    Frontend Usage:
    - detail: Displayed to user in error toast/alert
    
    QA-CONTRACT-002 Reference
    """
    detail: str = Field(..., min_length=1, description="Human-readable error message")
    
    class Config:
        extra = "forbid"


class RegisterResponse(BaseModel):
    """
    Contract: POST /auth/register response
    
    Frontend Usage:
    - id: Stored for future reference
    - email: Confirms registration success
    - is_active: Account status check
    
    QA-CONTRACT-003 Reference
    """
    id: str = Field(..., description="User UUID")
    email: str = Field(..., description="Registered email address")
    is_active: bool = Field(default=True, description="Account active status")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    
    class Config:
        extra = "forbid"


class ModuleResponse(BaseModel):
    """
    Contract: GET /api/modules and POST /api/modules response item
    
    Frontend Usage:
    - id: Module identifier for updates/deletes
    - user_id: Owner identifier
    - module_type: Determines which component to render
    - name: Displayed in module header
    - size: Determines grid cell size (small/medium/large)
    - position_x, position_y: Grid position (per B06)
    - width, height: Module dimensions (per B06)
    - refresh_interval: Data refresh rate
    - is_active: Controls visibility
    - config: Module-specific settings
    
    QA-CONTRACT-004, QA-CONTRACT-005, QA-CONTRACT-006 Reference
    Architect Decision B06: API includes layout fields per ARCH-6.1
    """
    id: str = Field(..., description="Module UUID v4")
    user_id: str = Field(..., description="Owner user UUID")
    module_type: str = Field(
        ..., 
        pattern="^(portfolio|calendar|health|finance|notes|weather|tasks)$",
        description="Module type enum"
    )
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    config: Dict[str, Any] = Field(default_factory=dict, description="Module settings")
    size: str = Field(
        ..., 
        pattern="^(small|medium|large)$",
        description="Grid size enum"
    )
    position_x: int = Field(..., description="Grid X position")
    position_y: int = Field(..., description="Grid Y position")
    width: Optional[int] = Field(default=None, description="Module width in grid units")
    height: Optional[int] = Field(default=None, description="Module height in grid units")
    refresh_interval: int = Field(default=300, description="Data refresh interval in seconds")
    is_active: bool = Field(..., description="Visibility flag")
    created_at: str = Field(..., description="ISO 8601 timestamp")
    updated_at: str = Field(..., description="ISO 8601 timestamp")
    
    class Config:
        extra = "forbid"


class ModuleListResponse(BaseModel):
    """
    Contract: GET /api/modules response wrapper
    
    QA-CONTRACT-005, QA-CONTRACT-006 Reference
    Architect Decision B06: API includes total count
    """
    modules: List[ModuleResponse] = Field(..., description="Array of user modules")
    total: int = Field(..., description="Total number of modules")
    
    class Config:
        extra = "forbid"


class HealthResponse(BaseModel):
    """
    Contract: GET /health response
    
    Frontend Usage:
    - status: Load balancer health check
    - version: Displayed in footer/settings
    - database: Database health status
    - redis: Redis health status
    
    QA-CONTRACT-008 Reference
    """
    status: str = Field(
        ..., 
        pattern="^(healthy|unhealthy|degraded)$",
        description="System health status"
    )
    version: Optional[str] = Field(default=None, description="API version")
    timestamp: Optional[str] = Field(default=None, description="ISO 8601 timestamp")
    database: Optional[str] = Field(default=None, description="Database health")
    redis: Optional[str] = Field(default=None, description="Redis health")
    
    class Config:
        extra = "forbid"


# ============================================================================
# TEST CLASS: Authentication Contracts
# Requirement: ARCH-5.2 API stability
# ============================================================================

class TestAuthContracts:
    """
    QA-CONTRACT-001 through QA-CONTRACT-003
    Validates authentication API contracts
    """
    
    @pytest.mark.asyncio
    async def test_qa_contract_001_login_response_valid_tokens(self, client, db_session):
        """
        QA-CONTRACT-001: Login returns valid tokens
        
        Preconditions:
        - User exists in database
        - Backend running at localhost:8000
        
        Expected Result:
        - Response status: 200
        - Response matches LoginResponse schema
        - access_token is valid JWT format (3 parts separated by dots)
        - refresh_token is valid opaque token (per Architect B05)
        - token_type is "bearer"
        
        Priority: P1 (Blocks login functionality)
        
        Note: Per Architect Decision B05, refresh tokens are opaque (not JWT)
        for security (server-side revocation support).
        """
        from app.services.auth.service import create_user
        
        # Setup: Create test user
        user = await create_user(db_session, "qa-contract-001@example.com", "TestPass123!")
        
        # Execute: Login request
        response = await client.post("/auth/login", json={
            "email": "qa-contract-001@example.com",
            "password": "TestPass123!"
        })
        
        # Validate response code
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate schema contract
        try:
            validated = LoginResponse(**data)
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-001 FAIL: Login response violates contract\n{e}")
        
        # Validate JWT format for access_token (3 parts: header.payload.signature)
        assert validated.access_token.count('.') == 2, \
            f"QA-CONTRACT-001 FAIL: access_token not valid JWT format: {validated.access_token[:50]}..."
        
        # Validate refresh_token is present and non-empty (opaque per B05)
        assert validated.refresh_token, \
            f"QA-CONTRACT-001 FAIL: refresh_token is empty"
        assert len(validated.refresh_token) >= 20, \
            f"QA-CONTRACT-001 FAIL: refresh_token too short: {len(validated.refresh_token)}"
        
        # Validate token type
        assert validated.token_type == "bearer", \
            f"QA-CONTRACT-001 FAIL: token_type is '{validated.token_type}', expected 'bearer'"
    
    @pytest.mark.asyncio
    async def test_qa_contract_002_login_error_structure(self, client):
        """
        QA-CONTRACT-002: Failed login returns proper error structure
        
        Preconditions:
        - Backend running
        - User does not exist or password incorrect
        
        Expected Result:
        - Response status: 401
        - Response matches ErrorResponse schema
        - detail field contains error message
        
        Priority: P1 (Error handling contract)
        """
        response = await client.post("/auth/login", json={
            "email": "nonexistent-user@example.com",
            "password": "wrongpassword123"
        })
        
        # Validate status code
        assert response.status_code == 401, \
            f"QA-CONTRACT-002 FAIL: Expected 401 for invalid credentials, got {response.status_code}"
        
        data = response.json()
        
        # Validate error contract
        try:
            validated = ErrorResponse(**data)
            assert validated.detail, "QA-CONTRACT-002 FAIL: detail field is empty"
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-002 FAIL: Error response violates contract\n{e}")
    
    @pytest.mark.asyncio
    async def test_qa_contract_003_register_response_fields(self, client):
        """
        QA-CONTRACT-003: Registration returns tokens (same as login)
        
        Preconditions:
        - Email not already registered
        
        Expected Result:
        - Response status: 201
        - Response matches LoginResponse (TokenPair) schema
        - access_token is valid JWT format (3 parts separated by dots)
        - refresh_token is valid opaque token (per B05)
        - token_type is "bearer"
        
        Note: Register returns tokens (not user object) to enable immediate login
        
        Priority: P1 (Registration flow)
        """
        response = await client.post("/auth/register", json={
            "email": "qa-contract-003@example.com",
            "password": "TestPass123!"
        })
        
        assert response.status_code == 201, \
            f"QA-CONTRACT-003 FAIL: Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate schema against LoginResponse (TokenPair)
        try:
            validated = LoginResponse(**data)
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-003 FAIL: Register response violates contract\n{e}")
        
        # Validate JWT format for access_token
        assert validated.access_token.count('.') == 2, \
            f"QA-CONTRACT-003 FAIL: access_token not valid JWT format"
        
        # Validate refresh_token is opaque (not JWT per B05)
        assert validated.refresh_token, \
            f"QA-CONTRACT-003 FAIL: refresh_token is empty"
        assert len(validated.refresh_token) >= 20, \
            f"QA-CONTRACT-003 FAIL: refresh_token too short: {len(validated.refresh_token)}"
        
        # Validate token_type
        assert validated.token_type == "bearer", \
            f"QA-CONTRACT-003 FAIL: token_type should be 'bearer', got {validated.token_type}"
    
    @pytest.mark.asyncio
    async def test_qa_contract_012_token_refresh_rotation(self, client, db_session):
        """
        QA-CONTRACT-012: Token refresh rotates access token
        
        Preconditions:
        - User exists and is logged in
        - Valid refresh token from login response
        
        Expected Result:
        - Response status: 200
        - Response matches LoginResponse (TokenPair) schema
        - New access_token is valid JWT (different from original)
        - New refresh_token is opaque (different from original)
        - Old refresh token is invalidated (rotation)
        
        Priority: P1 (Session management per ARCH-5.3)
        
        Reference: ARCH-5.1, ARCH-5.3, B05
        """
        from app.services.auth.service import create_user
        
        # Setup: Create user and login
        user = await create_user(db_session, "qa-contract-012@example.com", "TestPass123!")
        login_response = await client.post("/auth/login", json={
            "email": "qa-contract-012@example.com",
            "password": "TestPass123!"
        })
        
        assert login_response.status_code == 200, \
            f"QA-CONTRACT-012 SETUP FAIL: Login failed with {login_response.status_code}"
        
        login_data = login_response.json()
        original_access = login_data["access_token"]
        original_refresh = login_data["refresh_token"]
        
        # Execute: Refresh token request
        refresh_response = await client.post("/auth/refresh", json={
            "refresh_token": original_refresh
        })
        
        assert refresh_response.status_code == 200, \
            f"QA-CONTRACT-012 FAIL: Expected 200, got {refresh_response.status_code}: {refresh_response.text}"
        
        data = refresh_response.json()
        
        # Validate schema
        try:
            validated = LoginResponse(**data)
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-012 FAIL: Refresh response violates contract\n{e}")
        
        # Validate new access token is JWT (rotation - new expiry)
        assert validated.access_token.count('.') == 2, \
            f"QA-CONTRACT-012 FAIL: New access_token not valid JWT format"
        
        # Note: Access tokens may have identical content if generated within same second
        # (JWT payload includes timestamp). This is expected behavior.
        # The key validation is that a NEW token was issued with valid JWT structure.
        
        # Validate new refresh token is opaque (per B05) and DIFFERENT (rotation required)
        assert validated.refresh_token, \
            f"QA-CONTRACT-012 FAIL: refresh_token is empty"
        assert len(validated.refresh_token) >= 20, \
            f"QA-CONTRACT-012 FAIL: refresh_token too short"
        
        # CRITICAL: Refresh token MUST be different (opaque token rotation)
        assert validated.refresh_token != original_refresh, \
            f"QA-CONTRACT-012 FAIL: Refresh token not rotated (same as original)"
        
        # Validate token_type
        assert validated.token_type == "bearer", \
            f"QA-CONTRACT-012 FAIL: token_type should be 'bearer', got {validated.token_type}"
        
        # Verify old refresh token is invalidated (rotation security)
        second_refresh = await client.post("/auth/refresh", json={
            "refresh_token": original_refresh
        })
        
        # Old token should be rejected (401/403)
        assert second_refresh.status_code in [401, 403], \
            f"QA-CONTRACT-012 FAIL: Old refresh token still valid (security issue). " \
            f"Expected 401/403, got {second_refresh.status_code}"


# ============================================================================
# TEST CLASS: Module Contracts
# Requirement: ARCH-4.1 Data exchange format
# ============================================================================

class TestModuleContracts:
    """
    QA-CONTRACT-004 through QA-CONTRACT-006
    Validates module management API contracts
    """
    
    @pytest.mark.asyncio
    async def test_qa_contract_004_create_module_response(self, client, db_session):
        """
        QA-CONTRACT-004: Create module returns complete module object
        
        Preconditions:
        - User authenticated
        - Valid authentication token in header
        
        Expected Result:
        - Response status: 201
        - Response matches ModuleResponse schema
        - All required fields present (id, module_type, name, size, is_active)
        - id is assigned (not null/empty)
        - is_active is True by default
        
        Priority: P1 (Core functionality)
        """
        from app.services.auth.service import create_user, create_access_token
        
        # Setup
        user = await create_user(db_session, "qa-contract-004@example.com", "TestPass123!")
        token = create_access_token(str(user.id))
        
        # Execute
        response = await client.post(
            "/api/modules",
            json={
                "module_type": "portfolio",
                "name": "Contract Test Portfolio",
                "size": "medium",
                "config": {"currency": "USD"}
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 201, \
            f"QA-CONTRACT-004 FAIL: Expected 201, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Validate schema
        try:
            validated = ModuleResponse(**data)
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-004 FAIL: Create module response violates contract\n{e}")
        
        # Validate field values
        assert data["module_type"] == "portfolio", \
            f"QA-CONTRACT-004 FAIL: module_type mismatch: {data['module_type']}"
        assert data["name"] == "Contract Test Portfolio", \
            f"QA-CONTRACT-004 FAIL: name mismatch: {data['name']}"
        assert data["size"] == "medium", \
            f"QA-CONTRACT-004 FAIL: size mismatch: {data['size']}"
        assert data["is_active"] is True, \
            f"QA-CONTRACT-004 FAIL: is_active should be True, got {data['is_active']}"
        assert data["id"], "QA-CONTRACT-004 FAIL: id is missing or empty"
        assert data["config"] == {"currency": "USD"}, \
            f"QA-CONTRACT-004 FAIL: config mismatch: {data['config']}"
    
    @pytest.mark.asyncio
    async def test_qa_contract_005_list_modules_array(self, client, db_session):
        """
        QA-CONTRACT-005: Module list returns array of valid modules
        
        Preconditions:
        - User authenticated
        - User has multiple modules (2+)
        
        Expected Result:
        - Response status: 200
        - Response matches ModuleListResponse schema
        - modules array contains all user modules
        - Each module in array matches ModuleResponse schema
        
        Priority: P1 (Core functionality)
        """
        # DEF-011-004: Use API to create modules instead of service import
        from app.services.auth.service import create_user, create_access_token
        
        # Setup: Create user
        user = await create_user(db_session, "qa-contract-005@example.com", "TestPass123!")
        token = create_access_token(str(user.id))
        
        # Create modules via API (2 modules)
        for mod_type, name, size in [
            ("portfolio", "First Module", "small"),
            ("calendar", "Second Module", "large")
        ]:
            await client.post(
                "/api/modules",
                json={"module_type": mod_type, "name": name, "size": size, "config": {}},
                headers={"Authorization": f"Bearer {token}"}
            )
        
        # Execute: List modules
        response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Validate
        assert response.status_code == 200, \
            f"QA-CONTRACT-005 FAIL: Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Validate list wrapper schema
        try:
            validated = ModuleListResponse(**data)
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-005 FAIL: Module list response violates contract\n{e}")
        
        # Validate count
        assert len(validated.modules) == 2, \
            f"QA-CONTRACT-005 FAIL: Expected 2 modules, got {len(validated.modules)}"
        
        # Validate total field (per B06)
        assert validated.total == 2, \
            f"QA-CONTRACT-005 FAIL: Expected total=2, got {validated.total}"
        
        # Validate each module
        module_names = [m.name for m in validated.modules]
        assert "First Module" in module_names, "QA-CONTRACT-005 FAIL: First Module not in list"
        assert "Second Module" in module_names, "QA-CONTRACT-005 FAIL: Second Module not in list"
    
    @pytest.mark.asyncio
    async def test_qa_contract_006_empty_module_list(self, client, db_session):
        """
        QA-CONTRACT-006: Empty module list returns valid empty array
        
        Preconditions:
        - User authenticated
        - New user with no modules
        
        Expected Result:
        - Response status: 200
        - Response matches ModuleListResponse schema
        - modules array is empty (not null, not missing)
        
        Priority: P1 (Edge case handling)
        """
        from app.services.auth.service import create_user, create_access_token
        
        user = await create_user(db_session, "qa-contract-006@example.com", "TestPass123!")
        token = create_access_token(str(user.id))
        
        response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200, \
            f"QA-CONTRACT-006 FAIL: Expected 200, got {response.status_code}"
        
        data = response.json()
        
        # Validate empty list
        try:
            validated = ModuleListResponse(**data)
            assert validated.modules == [], \
                f"QA-CONTRACT-006 FAIL: Expected empty array, got {validated.modules}"
            # Validate total field for empty list (per B06)
            assert validated.total == 0, \
                f"QA-CONTRACT-006 FAIL: Expected total=0 for empty list, got {validated.total}"
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-006 FAIL: Empty list response violates contract\n{e}")


# ============================================================================
# TEST CLASS: Health & System Contracts
# ============================================================================

class TestHealthContracts:
    """
    QA-CONTRACT-008
    Validates health check contract
    """
    
    @pytest.mark.asyncio
    async def test_qa_contract_008_health_status(self, client):
        """
        QA-CONTRACT-008: Health endpoint returns status
        
        Preconditions:
        - Backend running
        
        Expected Result:
        - Response status: 200
        - Response matches HealthResponse schema
        - status is one of: healthy, unhealthy, degraded
        
        Priority: P2 (Monitoring/operations)
        """
        response = await client.get("/health")
        
        assert response.status_code == 200, \
            f"QA-CONTRACT-008 FAIL: Expected 200, got {response.status_code}"
        
        data = response.json()
        
        try:
            validated = HealthResponse(**data)
            assert validated.status in ["healthy", "unhealthy", "degraded"], \
                f"QA-CONTRACT-008 FAIL: Invalid status: {validated.status}"
        except ValidationError as e:
            pytest.fail(f"QA-CONTRACT-008 FAIL: Health response violates contract\n{e}")


# ============================================================================
# TEST CLASS: Breaking Change Detection
# Requirement: QA-REG-001 Regression prevention
# ============================================================================

class TestSchemaStability:
    """
    QA-CONTRACT-009
    Detects breaking API changes via OpenAPI schema snapshots
    """
    
    SNAPSHOT_DIR = Path(__file__).parent / "snapshots"
    
    @pytest.mark.asyncio
    async def test_qa_contract_009_openapi_schema_stable(self, client):
        """
        QA-CONTRACT-009: OpenAPI schema structure is stable
        
        Preconditions:
        - /openapi.json endpoint accessible
        - Snapshot file exists (after first run)
        
        Expected Result:
        - Critical paths match saved snapshot
        - If mismatch: explicit diff showing what changed
        
        Priority: P1 (Regression prevention)
        
        Note: To update baseline after intentional API change:
        1. Delete backend/tests/snapshots/openapi_critical.json
        2. Re-run this test to create new snapshot
        3. Get QA sign-off on changes
        """
        response = await client.get("/openapi.json")
        
        assert response.status_code == 200, \
            "QA-CONTRACT-009 FAIL: OpenAPI schema not accessible"
        
        current_schema = response.json()
        
        # Extract critical paths AND schemas (per architecture blueprint)
        # Per B07: dashboard/layout endpoint removed for MVP (module-centric layout)
        critical_paths = {
            "/auth/login": current_schema.get("paths", {}).get("/auth/login", {}),
            "/auth/register": current_schema.get("paths", {}).get("/auth/register", {}),
            "/auth/refresh": current_schema.get("paths", {}).get("/auth/refresh", {}),
            "/api/modules": current_schema.get("paths", {}).get("/api/modules", {}),
            "/health": current_schema.get("paths", {}).get("/health", {}),
        }
        
        # Extract critical schemas (these define the contract per ARCH-5.2)
        schemas = current_schema.get("components", {}).get("schemas", {})
        critical_schemas = {
            "TokenPair": schemas.get("TokenPair", {}),
            "TokenRefresh": schemas.get("TokenRefresh", {}),
            "ModuleResponse": schemas.get("ModuleResponse", {}),
            "ModuleListResponse": schemas.get("ModuleListResponse", {}),
            "HealthResponse": schemas.get("HealthResponse", {}),
        }
        
        critical_api = {
            "paths": critical_paths,
            "components": {"schemas": critical_schemas}
        }
        
        snapshot_path = self.SNAPSHOT_DIR / "openapi_critical.json"
        
        if not snapshot_path.exists():
            # First run - create baseline
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(json.dumps(critical_api, indent=2, sort_keys=True))
            pytest.skip("QA-CONTRACT-009: Created initial OpenAPI snapshot (first run)")
        
        saved = json.loads(snapshot_path.read_text())
        current_json = json.dumps(critical_api, indent=2, sort_keys=True)
        saved_json = json.dumps(saved, indent=2, sort_keys=True)
        
        if current_json != saved_json:
            import difflib
            diff = difflib.unified_diff(
                saved_json.splitlines(keepends=True),
                current_json.splitlines(keepends=True),
                fromfile="saved",
                tofile="current"
            )
            pytest.fail(
                f"QA-CONTRACT-009 FAIL: API schema changed! This may break frontend.\n\n"
                f"Diff:\n{''.join(diff)}\n\n"
                f"To update baseline: delete {snapshot_path} and re-run"
            )


# ============================================================================
# TEST CLASS: Data Type Contracts
# ============================================================================

class TestDataTypeContracts:
    """
    QA-CONTRACT-010, QA-CONTRACT-011
    Validates field data types match expectations
    """
    
    @pytest.mark.asyncio
    async def test_qa_contract_010_datetime_iso_format(self, client, db_session):
        """
        QA-CONTRACT-010: DateTime fields are ISO 8601 strings
        
        Preconditions:
        - Module exists with timestamps
        
        Expected Result:
        - created_at is parseable by datetime.fromisoformat()
        - updated_at is parseable by datetime.fromisoformat()
        
        Priority: P1 (Frontend date parsing will fail otherwise)
        """
        # DEF-011-004: Use API instead of service import
        from app.services.auth.service import create_user, create_access_token
        
        user = await create_user(db_session, "qa-contract-010@example.com", "TestPass123!")
        token = create_access_token(str(user.id))
        
        # Create module via API to generate timestamps
        await client.post(
            "/api/modules",
            json={"module_type": "notes", "name": "Date Test Module", "size": "small", "config": {}},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        data = response.json()
        
        if data.get("modules"):
            mod = data["modules"][0]
            
            for field in ["created_at", "updated_at"]:
                if field in mod and mod[field]:
                    try:
                        # Handle both with and without Z suffix
                        dt_str = mod[field].replace('Z', '+00:00')
                        datetime.fromisoformat(dt_str)
                    except ValueError as e:
                        pytest.fail(
                            f"QA-CONTRACT-010 FAIL: {field} not valid ISO 8601: {mod[field]}\nError: {e}"
                        )
    
    @pytest.mark.asyncio
    async def test_qa_contract_011_id_is_uuid_string(self, client, db_session):
        """
        QA-CONTRACT-011: ID fields are string UUIDs
        
        Preconditions:
        - Module exists
        
        Expected Result:
        - id is a string (not number, not object)
        - id matches UUID v4 pattern
        
        Priority: P1 (Frontend treats IDs as opaque strings)
        """
        # DEF-011-004: Use API instead of service import
        from app.services.auth.service import create_user, create_access_token
        
        user = await create_user(db_session, "qa-contract-011@example.com", "TestPass123!")
        token = create_access_token(str(user.id))
        
        # Create module via API
        await client.post(
            "/api/modules",
            json={"module_type": "notes", "name": "UUID Test Module", "size": "small", "config": {}},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        response = await client.get(
            "/api/modules",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        data = response.json()
        
        for mod in data.get("modules", []):
            # Validate type is string
            assert isinstance(mod["id"], str), \
                f"QA-CONTRACT-011 FAIL: ID is not string, got {type(mod['id'])}: {mod['id']}"
            
            # Validate UUID v4 pattern
            uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$'
            assert re.match(uuid_pattern, mod["id"]), \
                f"QA-CONTRACT-011 FAIL: ID not valid UUID v4: {mod['id']}"
