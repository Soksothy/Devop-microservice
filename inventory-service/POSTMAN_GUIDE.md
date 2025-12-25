# Postman Collection - Inventory Microservice API

## 📦 Import Instructions

1. Open Postman
2. Click **Import** button (top left)
3. Select the file: `Inventory_API.postman_collection.json`
4. Click **Import**

## 🚀 Quick Start

The collection is organized into 5 main folders:

### 1. **Health Check**
- Test if the service is running and database is connected

### 2. **Inventory Management**
- List all inventory items (with pagination)
- Get a specific product
- Create new inventory
- Update inventory quantity

### 3. **Stock Adjustments**
- Add stock (positive quantity)
- Subtract stock (negative quantity)
- Record damaged/lost items

### 4. **Test Scenarios**
- Create multiple products
- Test error handling (negative stock, not found, duplicates)

### 5. **Complete Workflow Example**
Follow this workflow to see a real-world example:
1. Create iPhone 15 Pro (100 units)
2. Check initial stock
3. Customer buys 5 units (-5)
4. Receive new shipment (+50)
5. Record damaged item (-1)
6. Final stock check (should be 144 units)

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/inventory/items` | List all items (paginated) |
| GET | `/api/v1/inventory/items/{product_id}` | Get single item |
| POST | `/api/v1/inventory/items` | Create new item |
| PUT | `/api/v1/inventory/items/{product_id}` | Update quantity |
| POST | `/api/v1/inventory/items/{product_id}/adjust` | Adjust stock (+/-) |

## 🔧 Configuration

The collection uses variables:
- `baseUrl`: `http://localhost:8001`
- `apiVersion`: `v1`

Change these if your setup differs.

## 💡 Usage Examples

### Create Product
```json
POST /api/v1/inventory/items
{
  "product_id": "PROD-001",
  "quantity": 100,
  "warehouse_location": "WH-A1"
}
```

### Add Stock (Restock)
```json
POST /api/v1/inventory/items/PROD-001/adjust
{
  "quantity": 50,
  "reason": "Restocked from supplier"
}
```

### Subtract Stock (Sale)
```json
POST /api/v1/inventory/items/PROD-001/adjust
{
  "quantity": -5,
  "reason": "Sold to customer"
}
```

### Update Absolute Quantity
```json
PUT /api/v1/inventory/items/PROD-001
{
  "quantity": 150,
  "reason": "Manual inventory count"
}
```

## ✅ Expected Results

All requests should return JSON responses:

**Success (200/201):**
```json
{
  "product_id": "PROD-001",
  "quantity": 100,
  "warehouse_location": "WH-A1",
  "created_at": "2025-12-25T10:00:00Z",
  "updated_at": "2025-12-25T10:00:00Z"
}
```

**Error (400/404/500):**
```json
{
  "detail": {
    "detail": "Error message",
    "code": "ERROR_CODE"
  }
}
```

## 🧪 Testing Tips

1. **Start with Health Check** - Ensure the service is running
2. **Run Complete Workflow** - Follow the numbered sequence in the "Complete Workflow Example" folder
3. **Test Error Cases** - Try the test scenarios to see error handling
4. **Use Variables** - The collection includes product_id variables for easy testing

## 🐛 Troubleshooting

**Connection Refused:**
- Check Docker containers are running: `docker ps`
- Ensure port 8001 is not in use
- Restart containers: `docker-compose restart`

**Database Errors:**
- Check MongoDB is healthy: `docker logs inventory-mongodb`
- Restart services: `docker-compose down && docker-compose up -d`

**404 Not Found:**
- Ensure you've created the product first
- Check product_id spelling

## 📚 API Documentation

For complete API documentation, visit:
- Swagger UI: http://localhost:8001/api/v1/docs
- ReDoc: http://localhost:8001/api/v1/redoc

## 🎯 Common Workflows

### Daily Operations
1. Check stock levels (GET /items)
2. Process sales (POST /adjust with negative quantity)
3. Receive shipments (POST /adjust with positive quantity)

### Inventory Management
1. Add new products (POST /items)
2. Update stock counts (PUT /items/{id})
3. Record adjustments (POST /adjust)

### Reporting
1. List all items with pagination
2. Filter by product_id
3. Track changes via stock_movements (MongoDB)

---

**Ready to test!** 🚀

Start with the "Complete Workflow Example" for a guided tour of all features.
