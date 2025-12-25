"""
Comprehensive test suite for Inventory API.
Tests all endpoints with mocked MongoDB and validation scenarios.
"""

import pytest
from httpx import AsyncClient
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from fastapi import status

from app.main import app
from app.database import get_database


# Mock MongoDB database
@pytest.fixture
def mock_db():
    """Create a mock MongoDB database for testing."""
    db = MagicMock()
    db.inventory = MagicMock()
    db.stock_movements = MagicMock()
    db.command = AsyncMock(return_value={"ok": 1})
    return db


@pytest.fixture
def mock_inventory_data():
    """Sample inventory data for testing."""
    return {
        "_id": "507f1f77bcf86cd799439011",
        "product_id": "PROD-001",
        "quantity": 100,
        "warehouse_location": "WH-A1",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


# Override database dependency for testing
@pytest.fixture
def client(mock_db):
    """Create test client with mocked database."""
    app.dependency_overrides[get_database] = lambda: mock_db
    return AsyncClient(app=app, base_url="http://test")


class TestHealthEndpoint:
    """Test health check endpoint."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, client, mock_db):
        """Test successful health check."""
        async with client as ac:
            response = await ac.get("/api/v1/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "environment" in data
        assert "database" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_health_check_db_failure(self, client, mock_db):
        """Test health check with database failure."""
        mock_db.command = AsyncMock(side_effect=Exception("Connection failed"))
        
        async with client as ac:
            response = await ac.get("/api/v1/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["database"] == "disconnected"


class TestListInventory:
    """Test inventory listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_inventory_success(self, client, mock_db, mock_inventory_data):
        """Test successful inventory listing."""
        mock_db.inventory.count_documents = AsyncMock(return_value=1)
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[mock_inventory_data])
        mock_db.inventory.find.return_value = mock_cursor
        
        async with client as ac:
            response = await ac.get("/api/v1/inventory/items")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "current_page" in data
        assert "per_page" in data
        assert "total" in data
        assert "last_page" in data
        assert "data" in data
        assert len(data["data"]) > 0
    
    @pytest.mark.asyncio
    async def test_list_inventory_with_pagination(self, client, mock_db):
        """Test inventory listing with pagination parameters."""
        mock_db.inventory.count_documents = AsyncMock(return_value=0)
        mock_cursor = MagicMock()
        mock_cursor.skip.return_value = mock_cursor
        mock_cursor.limit.return_value = mock_cursor
        mock_cursor.sort.return_value = mock_cursor
        mock_cursor.to_list = AsyncMock(return_value=[])
        mock_db.inventory.find.return_value = mock_cursor
        
        async with client as ac:
            response = await ac.get("/api/v1/inventory/items?page=2&limit=10")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["current_page"] == 2
        assert data["per_page"] == 10


class TestGetInventory:
    """Test get single inventory endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_inventory_success(self, client, mock_db, mock_inventory_data):
        """Test successful inventory retrieval."""
        mock_db.inventory.find_one = AsyncMock(return_value=mock_inventory_data)
        
        async with client as ac:
            response = await ac.get("/api/v1/inventory/items/PROD-001")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["product_id"] == "PROD-001"
        assert "quantity" in data
        assert "warehouse_location" in data
    
    @pytest.mark.asyncio
    async def test_get_inventory_not_found(self, client, mock_db):
        """Test inventory retrieval for non-existent product."""
        mock_db.inventory.find_one = AsyncMock(return_value=None)
        
        async with client as ac:
            response = await ac.get("/api/v1/inventory/items/NONEXISTENT")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data


class TestCreateInventory:
    """Test create inventory endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_inventory_success(self, client, mock_db):
        """Test successful inventory creation."""
        mock_db.inventory.find_one = AsyncMock(return_value=None)
        mock_db.inventory.insert_one = AsyncMock(return_value=MagicMock(inserted_id="507f1f77bcf86cd799439011"))
        mock_db.stock_movements.insert_one = AsyncMock()
        
        payload = {
            "product_id": "PROD-002",
            "quantity": 50,
            "warehouse_location": "WH-B1"
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items", json=payload)
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["product_id"] == "PROD-002"
        assert data["quantity"] == 50
    
    @pytest.mark.asyncio
    async def test_create_inventory_duplicate(self, client, mock_db, mock_inventory_data):
        """Test creating inventory for existing product."""
        mock_db.inventory.find_one = AsyncMock(return_value=mock_inventory_data)
        
        payload = {
            "product_id": "PROD-001",
            "quantity": 50,
            "warehouse_location": "WH-B1"
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items", json=payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    @pytest.mark.asyncio
    async def test_create_inventory_invalid_quantity(self, client):
        """Test creating inventory with negative quantity."""
        payload = {
            "product_id": "PROD-003",
            "quantity": -10,
            "warehouse_location": "WH-C1"
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestUpdateInventory:
    """Test update inventory endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_inventory_success(self, client, mock_db, mock_inventory_data):
        """Test successful inventory update."""
        mock_db.inventory.find_one = AsyncMock(return_value=mock_inventory_data)
        mock_db.inventory.update_one = AsyncMock()
        mock_db.stock_movements.insert_one = AsyncMock()
        
        payload = {
            "quantity": 150,
            "reason": "Restocking"
        }
        
        async with client as ac:
            response = await ac.put("/api/v1/inventory/items/PROD-001", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_update_inventory_not_found(self, client, mock_db):
        """Test updating non-existent inventory."""
        mock_db.inventory.find_one = AsyncMock(return_value=None)
        
        payload = {
            "quantity": 150
        }
        
        async with client as ac:
            response = await ac.put("/api/v1/inventory/items/NONEXISTENT", json=payload)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestAdjustStock:
    """Test stock adjustment endpoint."""
    
    @pytest.mark.asyncio
    async def test_adjust_stock_add(self, client, mock_db, mock_inventory_data):
        """Test adding stock via adjustment."""
        mock_db.inventory.find_one = AsyncMock(return_value=mock_inventory_data)
        mock_db.inventory.update_one = AsyncMock()
        mock_db.stock_movements.insert_one = AsyncMock()
        
        payload = {
            "quantity": 10,
            "reason": "Restocked"
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items/PROD-001/adjust", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_adjust_stock_subtract(self, client, mock_db, mock_inventory_data):
        """Test subtracting stock via adjustment."""
        mock_db.inventory.find_one = AsyncMock(return_value=mock_inventory_data)
        mock_db.inventory.update_one = AsyncMock()
        mock_db.stock_movements.insert_one = AsyncMock()
        
        payload = {
            "quantity": -5,
            "reason": "Sold"
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items/PROD-001/adjust", json=payload)
        
        assert response.status_code == status.HTTP_200_OK
    
    @pytest.mark.asyncio
    async def test_adjust_stock_negative_result(self, client, mock_db, mock_inventory_data):
        """Test adjustment that would result in negative stock."""
        mock_inventory_data["quantity"] = 5
        mock_db.inventory.find_one = AsyncMock(return_value=mock_inventory_data)
        
        payload = {
            "quantity": -10,  # More than available
            "reason": "Sale attempt"
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items/PROD-001/adjust", json=payload)
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "Insufficient stock" in data["detail"]


class TestValidation:
    """Test input validation."""
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client):
        """Test creating inventory without required fields."""
        payload = {
            "product_id": "PROD-004"
            # Missing quantity and warehouse_location
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    @pytest.mark.asyncio
    async def test_adjust_missing_reason(self, client):
        """Test adjustment without reason."""
        payload = {
            "quantity": 10
            # Missing reason
        }
        
        async with client as ac:
            response = await ac.post("/api/v1/inventory/items/PROD-001/adjust", json=payload)
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY