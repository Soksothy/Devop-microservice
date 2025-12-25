"""
MongoDB models and business logic for inventory management.
Handles inventory operations and stock movements with proper validation.
"""

from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas import (
    InventoryCreateRequest,
    InventoryUpdateRequest,
    StockAdjustRequest,
    InventoryResponse
)
import logging

logger = logging.getLogger(__name__)


class InventoryModel:
    """
    Business logic for inventory management operations.
    Implements stock reservation, release, and deduction with proper validation.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.inventory
        self.movements_collection = db.stock_movements
    
    async def create_inventory(self, data: InventoryCreateRequest) -> dict:
        """
        Create a new inventory record.
        
        Args:
            data: Inventory creation request data
            
        Returns:
            Created inventory document
            
        Raises:
            ValueError: If product_id already exists
        """
        # Check if product already exists
        existing = await self.collection.find_one({"product_id": data.product_id})
        if existing:
            raise ValueError(f"Product {data.product_id} already exists in inventory")
        
        now = datetime.utcnow()
        inventory_doc = {
            "product_id": data.product_id,
            "quantity": data.quantity,
            "warehouse_location": data.warehouse_location,
            "created_at": now,
            "updated_at": now
        }
        
        result = await self.collection.insert_one(inventory_doc)
        inventory_doc["_id"] = result.inserted_id
        
        # Log stock movement for initial stock
        if data.quantity > 0:
            await self._log_movement(
                product_id=data.product_id,
                quantity_change=data.quantity,
                new_quantity=data.quantity,
                reason="Initial stock creation"
            )
        
        logger.info(f"Created inventory for product {data.product_id} with quantity {data.quantity}")
        return inventory_doc
    
    async def get_inventory(self, product_id: str) -> Optional[dict]:
        """
        Get inventory record for a specific product.
        
        Args:
            product_id: Product identifier
            
        Returns:
            Inventory document
        """
        inventory = await self.collection.find_one({"product_id": product_id})
        return inventory
    
    async def list_inventory(
        self,
        skip: int = 0,
        limit: int = 20,
        product_id: Optional[str] = None
    ) -> tuple[list[dict], int]:
        """
        List inventory items with pagination and optional filtering.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            product_id: Optional product ID filter
            
        Returns:
            Tuple of (inventory list, total count)
        """
        query = {}
        if product_id:
            query["product_id"] = product_id
        
        # Get total count
        total = await self.collection.count_documents(query)
        
        # Get paginated results
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("updated_at", -1)
        items = await cursor.to_list(length=limit)
        
        return items, total
    
    async def update_inventory(self, product_id: str, data: InventoryUpdateRequest) -> dict:
        """
        Update inventory quantity.
        
        Args:
            product_id: Product identifier
            data: Update request data
            
        Returns:
            Updated inventory document
            
        Raises:
            ValueError: If product not found
        """
        inventory = await self.get_inventory(product_id)
        if not inventory:
            raise ValueError(f"Product {product_id} not found")
        
        now = datetime.utcnow()
        old_quantity = inventory["quantity"]
        
        await self.collection.update_one(
            {"product_id": product_id},
            {"$set": {"quantity": data.quantity, "updated_at": now}}
        )
        
        # Log movement
        quantity_change = data.quantity - old_quantity
        await self._log_movement(
            product_id=product_id,
            quantity_change=quantity_change,
            new_quantity=data.quantity,
            reason=data.reason or "Manual update"
        )
        
        logger.info(f"Updated inventory for product {product_id} to quantity {data.quantity}")
        return await self.get_inventory(product_id)
    
    async def adjust_stock(self, product_id: str, data: StockAdjustRequest) -> dict:
        """
        Adjust stock by adding or subtracting quantity.
        
        Args:
            product_id: Product identifier
            data: Adjust request data (positive to add, negative to subtract)
            
        Returns:
            Updated inventory document
            
        Raises:
            ValueError: If product not found or would result in negative stock
        """
        inventory = await self.get_inventory(product_id)
        if not inventory:
            raise ValueError(f"Product {product_id} not found")
        
        new_quantity = inventory["quantity"] + data.quantity
        
        # Prevent negative stock
        if new_quantity < 0:
            raise ValueError(
                f"Insufficient stock. Current quantity: {inventory['quantity']}, "
                f"Requested change: {data.quantity}, "
                f"Would result in: {new_quantity}"
            )
        
        # Update quantity
        await self.collection.update_one(
            {"product_id": product_id},
            {
                "$set": {
                    "quantity": new_quantity,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Log movement
        await self._log_movement(
            product_id=product_id,
            quantity_change=data.quantity,
            new_quantity=new_quantity,
            reason=data.reason
        )
        
        logger.info(f"Adjusted stock for product {product_id} by {data.quantity} to {new_quantity}")
        return await self.get_inventory(product_id)
    
    async def _log_movement(
        self,
        product_id: str,
        quantity_change: int,
        new_quantity: int,
        reason: str
    ):
        """
        Log stock movement to audit trail.
        
        Args:
            product_id: Product identifier
            quantity_change: Quantity changed (positive or negative)
            new_quantity: New quantity after change
            reason: Reason for movement
        """
        movement_doc = {
            "product_id": product_id,
            "quantity_change": quantity_change,
            "new_quantity": new_quantity,
            "reason": reason,
            "created_at": datetime.utcnow()
        }
        
        await self.movements_collection.insert_one(movement_doc)
        logger.debug(f"Logged movement for product {product_id}: {quantity_change} (reason: {reason})")
