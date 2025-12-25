"""
Inventory API router with all endpoints.
Implements RESTful operations with proper error handling and pagination.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime
import math
import logging

from app.database import get_database
from app.models.inventory import InventoryModel
from app.schemas import (
    InventoryCreateRequest,
    InventoryUpdateRequest,
    StockAdjustRequest,
    InventoryResponse,
    PaginatedInventoryResponse,
    HealthResponse,
    SuccessResponse,
    ErrorResponse
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check(db: AsyncIOMotorDatabase = Depends(get_database)):
    """
    Health check endpoint to verify service and database connectivity.
    
    Returns:
        Health status with environment info and database connectivity
    """
    try:
        # Verify database connection
        await db.command('ping')
        db_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy" if db_status == "connected" else "degraded",
        environment=settings.ENVIRONMENT,
        database=db_status,
        timestamp=datetime.utcnow()
    )


@router.get("/inventory/items", response_model=PaginatedInventoryResponse, tags=["Inventory"])
async def list_inventory(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="Items per page"
    ),
    product_id: str = Query(None, description="Filter by product ID"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    List all inventory items with pagination and optional filtering.
    
    Args:
        page: Page number (1-indexed)
        limit: Number of items per page
        product_id: Optional product ID filter
        
    Returns:
        Paginated list of inventory items
    """
    try:
        model = InventoryModel(db)
        skip = (page - 1) * limit
        
        items, total = await model.list_inventory(
            skip=skip,
            limit=limit,
            product_id=product_id
        )
        
        # Calculate pagination metadata
        last_page = math.ceil(total / limit) if total > 0 else 1
        
        # Convert to response models
        inventory_items = [
            InventoryResponse(
                product_id=item["product_id"],
                quantity=item["quantity"],
                warehouse_location=item["warehouse_location"],
                created_at=item["created_at"],
                updated_at=item["updated_at"]
            )
            for item in items
        ]
        
        return PaginatedInventoryResponse(
            current_page=page,
            per_page=limit,
            total=total,
            last_page=last_page,
            data=inventory_items
        )
        
    except Exception as e:
        logger.error(f"Error listing inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/inventory/items/{product_id}", response_model=InventoryResponse, tags=["Inventory"])
async def get_inventory_item(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get inventory details for a specific product.
    
    Args:
        product_id: Product identifier
        
    Returns:
        Inventory details including available stock
        
    Raises:
        HTTPException: 404 if product not found
    """
    try:
        model = InventoryModel(db)
        inventory = await model.get_inventory(product_id)
        
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return InventoryResponse(
            product_id=inventory["product_id"],
            quantity=inventory["quantity"],
            warehouse_location=inventory["warehouse_location"],
            created_at=inventory["created_at"],
            updated_at=inventory["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting inventory for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post(
    "/inventory/items",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Inventory"]
)
async def create_inventory_item(
    data: InventoryCreateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Create a new inventory record.
    
    Args:
        data: Inventory creation data
        
    Returns:
        Created inventory record
        
    Raises:
        HTTPException: 400 if product already exists
    """
    try:
        model = InventoryModel(db)
        inventory = await model.create_inventory(data)
        
        return InventoryResponse(
            product_id=inventory["product_id"],
            quantity=inventory["quantity"],
            warehouse_location=inventory["warehouse_location"],
            created_at=inventory["created_at"],
            updated_at=inventory["updated_at"]
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating inventory: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/inventory/items/{product_id}", response_model=InventoryResponse, tags=["Inventory"])
async def update_inventory_item(
    product_id: str,
    data: InventoryUpdateRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update inventory on-hand quantity.
    
    Args:
        product_id: Product identifier
        data: Update data
        
    Returns:
        Updated inventory record
        
    Raises:
        HTTPException: 404 if product not found, 400 if invalid update
    """
    try:
        model = InventoryModel(db)
        inventory = await model.update_inventory(product_id, data)
        
        return InventoryResponse(
            product_id=inventory["product_id"],
            quantity=inventory["quantity"],
            warehouse_location=inventory["warehouse_location"],
            created_at=inventory["created_at"],
            updated_at=inventory["updated_at"]
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Error updating inventory for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/inventory/items/{product_id}/adjust", response_model=InventoryResponse, tags=["Stock Operations"])
async def adjust_stock(
    product_id: str,
    data: StockAdjustRequest,
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Adjust stock quantity (add or subtract).
    Use positive values to add stock, negative values to subtract.
    
    Args:
        product_id: Product identifier
        data: Adjust request data (quantity can be positive or negative)
        
    Returns:
        Updated inventory with adjusted stock
        
    Raises:
        HTTPException: 404 if product not found, 400 if would result in negative stock
    """
    try:
        model = InventoryModel(db)
        inventory = await model.adjust_stock(product_id, data)
        
        return InventoryResponse(
            product_id=inventory["product_id"],
            quantity=inventory["quantity"],
            warehouse_location=inventory["warehouse_location"],
            created_at=inventory["created_at"],
            updated_at=inventory["updated_at"]
        )
        
    except ValueError as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
    except Exception as e:
        logger.error(f"Error adjusting stock for {product_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
