"""
MongoDB database connection and management.
Uses Motor for async MongoDB operations.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import IndexModel, ASCENDING
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager."""
    
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db_instance = Database()


async def connect_to_mongo():
    """
    Establish connection to MongoDB and create indexes.
    Called on application startup.
    """
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}")
        
        # Create MongoDB client with connection pooling
        db_instance.client = AsyncIOMotorClient(
            settings.MONGODB_URI,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000
        )
        
        # Get database instance
        db_instance.db = db_instance.client[settings.DATABASE_NAME]
        
        # Verify connection
        await db_instance.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB")
        
        # Create indexes for better performance
        await create_indexes()
        
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """
    Close MongoDB connection.
    Called on application shutdown.
    """
    try:
        if db_instance.client:
            db_instance.client.close()
            logger.info("MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {e}")


async def create_indexes():
    """Create database indexes for optimized queries."""
    try:
        # Index on product_id for inventory collection
        inventory_indexes = [
            IndexModel([("product_id", ASCENDING)], unique=True, name="product_id_idx"),
            IndexModel([("warehouse_location", ASCENDING)], name="warehouse_location_idx"),
            IndexModel([("updated_at", ASCENDING)], name="updated_at_idx")
        ]
        await db_instance.db.inventory.create_indexes(inventory_indexes)
        logger.info("Created indexes on inventory collection")
        
        # Index on product_id and created_at for stock_movements collection
        movements_indexes = [
            IndexModel([("product_id", ASCENDING)], name="movement_product_id_idx"),
            IndexModel([("created_at", ASCENDING)], name="movement_created_at_idx"),
            IndexModel([("order_id", ASCENDING)], name="movement_order_id_idx")
        ]
        await db_instance.db.stock_movements.create_indexes(movements_indexes)
        logger.info("Created indexes on stock_movements collection")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        raise


def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency to get database instance.
    
    Returns:
        AsyncIOMotorDatabase: Database instance
    """
    return db_instance.db
