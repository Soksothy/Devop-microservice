"""
Pydantic schemas for request validation and response serialization.
"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional, List


# Request Schemas
class InventoryCreateRequest(BaseModel):
    """Request schema for creating inventory record."""
    product_id: str = Field(..., description="Unique product identifier (UUID)")
    quantity: int = Field(..., ge=0, description="Initial quantity")
    warehouse_location: str = Field(..., min_length=1, description="Warehouse location code")
    
    @field_validator('quantity')
    @classmethod
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError("Quantity cannot be negative")
        return v


class InventoryUpdateRequest(BaseModel):
    """Request schema for updating inventory quantity."""
    quantity: int = Field(..., ge=0, description="New quantity")
    reason: Optional[str] = Field(None, description="Reason for update")


class StockAdjustRequest(BaseModel):
    """Request schema for adjusting stock (add or subtract)."""
    quantity: int = Field(..., description="Quantity change (positive to add, negative to subtract)")
    reason: str = Field(..., min_length=1, description="Reason for adjustment")


class StockCheckRequest(BaseModel):
    """Request schema for checking stock availability (used by order service)."""
    product_id: str = Field(..., description="Product identifier")
    required_quantity: int = Field(..., gt=0, description="Required quantity to check")


class BulkStockCheckRequest(BaseModel):
    """Request schema for checking multiple products stock availability."""
    items: List[StockCheckRequest] = Field(..., min_length=1, description="List of products to check")


# Response Schemas
class InventoryResponse(BaseModel):
    """Response schema for inventory item."""
    product_id: str
    quantity: int
    warehouse_location: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StockMovementResponse(BaseModel):
    """Response schema for stock movement."""
    id: str
    product_id: str
    quantity_change: int
    new_quantity: int
    reason: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class StockAvailabilityResponse(BaseModel):
    """Response schema for stock availability check."""
    product_id: str
    available: bool
    current_quantity: int
    required_quantity: int
    warehouse_location: str


class BulkStockAvailabilityResponse(BaseModel):
    """Response schema for bulk stock availability check."""
    all_available: bool
    items: List[StockAvailabilityResponse]


class PaginatedInventoryResponse(BaseModel):
    """Paginated response schema for inventory listing."""
    current_page: int
    per_page: int
    total: int
    last_page: int
    data: List[InventoryResponse]


class HealthResponse(BaseModel):
    """Health check response schema."""
    status: str
    environment: str
    database: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    code: str


class SuccessResponse(BaseModel):
    """Generic success response schema."""
    message: str
    data: Optional[dict] = None
