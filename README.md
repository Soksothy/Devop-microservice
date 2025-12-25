# Inventory Microservice

A production-ready FastAPI microservice for managing e-commerce inventory with MongoDB, featuring simple stock tracking with adjustments and comprehensive audit trails.

## 🚀 Features

- **RESTful API** with versioning (`/api/v1`)
- **Async/Await** operations for high performance
- **MongoDB** with Motor (async driver) and connection pooling
- **Simple Stock Tracking**: Single quantity field with add/subtract adjustments
- **Audit Trail**: Complete stock movement history
- **Pagination**: Efficient data retrieval with configurable limits
- **Docker Support**: Multi-stage builds with health checks
- **CI/CD Pipeline**: Automated testing, linting, and deployment
- **Comprehensive Tests**: pytest with async support and mocking
- **Production-Ready**: Exception handling, logging, CORS, non-root containers

## 📋 Prerequisites

- Python 3.11+
- MongoDB 7.0+
- Docker & Docker Compose (optional)
- Git

## 🛠️ Setup Instructions

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Devop02/inventory-service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start MongoDB locally**
   ```bash
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:7.0
   
   # Or install MongoDB locally
   ```

6. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload --port 8001
   ```

7. **Access the API documentation**
   - Swagger UI: http://localhost:8001/api/v1/docs
   - ReDoc: http://localhost:8001/api/v1/redoc

### Docker Setup

1. **Using Docker Compose (Recommended)**
   ```bash
   cd inventory-service
   docker-compose up -d
   ```
   This starts both the API service and MongoDB with persistent volumes.

2. **Build and run manually**
   ```bash
   # Build image
   docker build -t inventory-service .
   
   # Run container
   docker run -d -p 8001:8001 \
     -e MONGODB_URI=mongodb://host.docker.internal:27017 \
     -e DATABASE_NAME=inventory_db \
     inventory-service
   ```

3. **View logs**
   ```bash
   docker-compose logs -f inventory-api
   ```

4. **Stop services**
   ```bash
   docker-compose down
   ```

## 📚 API Documentation

### Base URL
```
http://localhost:8001/api/v1
```

### Endpoints

#### Health Check
```http
GET /api/v1/health
```
Returns service health status and database connectivity.

#### List Inventory Items
```http
GET /api/v1/inventory/items?page=1&limit=20&product_id=PROD-001
```
Returns paginated list of inventory items.

**Query Parameters:**
- `page` (integer): Page number (default: 1)
- `limit` (integer): Items per page (default: 20, max: 100)
- `product_id` (string, optional): Filter by product ID

**Response:**
```json
{
  "current_page": 1,
  "per_page": 20,
  "total": 100,
  "last_page": 5,
  "data": [
    {
      "product_id": "PROD-001",
      "quantity": 100,
      "warehouse_location": "WH-A1",
      "created_at": "2025-12-01T10:00:00Z",
      "updated_at": "2025-12-25T10:00:00Z"
    }
  ]
}
```

#### Get Inventory Item
```http
GET /api/v1/inventory/items/{product_id}
```
Returns inventory details for a specific product.

#### Create Inventory Item
```http
POST /api/v1/inventory/items
Content-Type: application/json

{
  "product_id": "PROD-001",
  "quantity": 100,
  "warehouse_location": "WH-A1"
}
```
Creates a new inventory record.

#### Update Inventory Quantity
```http
PUT /api/v1/inventory/items/{product_id}
Content-Type: application/json

{
  "quantity": 150,
  "reason": "Restocking"
}
```
Updates quantity for a product (sets absolute value).

#### Adjust Stock
```http
POST /api/v1/inventory/items/{product_id}/adjust
Content-Type: application/json

{
  "quantity": 10,
  "reason": "Restocked"
}
```
Adjusts stock by adding or subtracting. Use positive values to add stock, negative values to subtract.

**Examples:**
- Add stock: `{"quantity": 10, "reason": "Restocked"}`
- Subtract stock: `{"quantity": -5, "reason": "Sold"}`

**Business Rule:** Prevents negative stock - validates `current_quantity + quantity_change >= 0`

### Error Responses

All endpoints return consistent error format:
```json
{
  "detail": "Error message",
  "code": "ERROR_CODE"
}
```

**HTTP Status Codes:**
- `200 OK`: Successful operation
- `201 Created`: Resource created
- `400 Bad Request`: Invalid input or business rule violation
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## 🗄️ MongoDB Schema

### inventory Collection
```json
{
  "_id": "ObjectId",
  "product_id": "string (UUID, unique index)",
  "quantity": "int",
  "warehouse_location": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Indexes:**
- `product_id` (unique)
- `warehouse_location`
- `updated_at`

### stock_movements Collection
```json
{
  "_id": "ObjectId",
  "product_id": "string",
  "quantity_change": "int (can be positive or negative)",
  "new_quantity": "int",
  "reason": "string",
  "created_at": "datetime"
}
```

**Indexes:**
- `product_id`
- `created_at`

## 🧪 Testing

### Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_inventory.py -v

# Run specific test class
pytest tests/test_inventory.py::TestReserveStock -v
```

### Test Coverage
The test suite covers:
- ✅ All API endpoints
- ✅ Business logic validation
- ✅ Error handling scenarios
- ✅ Input validation
- ✅ Reserve/Release/Deduct operations
- ✅ Insufficient stock scenarios
- ✅ MongoDB mocking
 (6 endpoints)
- ✅ Business logic validation
- ✅ Error handling scenarios
- ✅ Input validation
- ✅ Stock adjustment operations (add/subtract)
- ✅ Negative stock preventionalhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `inventory_db` | Database name |
| `PORT` | `8001` | Application port |
| `ENVIRONMENT` | `development` | Environment (development/production) |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated) |
| `DEFAULT_PAGE_SIZE` | `20` | Default pagination size |
| `MAX_PAGE_SIZE` | `100` | Maximum pagination size |

## 🚢 CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline automatically:

1. **On Pull Request & Push to Main:**
   - Checks out code
   - Sets up Python 3.11
   - Installs dependencies
   - Runs pytest with coverage
   - Lints code with ruff

2. **On Push to Main (Additional):**
   - Builds Docker image
   - Pushes to Docker Hub with tags:
     - `latest`
     - `main-{SHA}`
   - Uses layer caching for faster builds

### Required Secrets

Configure these secrets in GitHub repository settings:
- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password or access token

### Pipeline Status

View pipeline status in the Actions tab of your GitHub repository.

## 📝 Business Logic

### Simple Stock Tracking
- Single `quantity` field tracks current stock
- No complex reserved/available calculations
- Straightforward add/subtract operations

### Adjust Operation
1. Get current quantity
2. Calculate: `new_quantity = current_quantity + quantity_change`
3. Validate: `new_quantity >= 0` (prevent negative stock)
4. Update quantity
5. Log movement with change and new total

### Audit Trail
All operations are logged to `stock_movements` collection with:
- Product ID
- Quantity change (positive or negative)
- New quantity after change
- Reason for change
- Timestamp

## 🔒 Security Features

- Non-root user in Docker container
- Environment variable configuration
- CORS middleware
- Input validation with Pydantic
- Error message sanitization
- No sensitive data in logs

## 🏗️ Project Structure

```
inventory-service/
├── app/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application & middleware
│   ├── config.py                # Configuration management
│   ├── database.py              # MongoDB connection & indexes
│   ├── schemas.py               # Pydantic models
│   ├── models/
│   │   ├── __init__.py
│   │   └── inventory.py         # Business logic & data models
│   └── routers/
│       ├── __init__.py
│       └── inventory.py         # API endpoints
├── tests/
│   ├── __init__.py
│   └── test_inventory.py        # Comprehensive test suite
├── .github/
│   └── workflows/
│       └── ci-cd.yml            # GitHub Actions pipeline
├── Dockerfile                   # Multi-stage Docker build
├── docker-compose.yml           # Service orchestration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .dockerignore               # Docker build exclusions
├── .gitignore                  # Git exclusions
└── README.md                   # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB is running
docker ps | grep mongo

# View MongoDB logs
docker logs mongodb

# Test connection
mongosh mongodb://localhost:27017
```

### Port Already in Use
```bash
# Find process using port 8001
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8001

# Kill the process or change PORT in .env
```

### Docker Build Fails
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
```

## 📞 Support

For issues and questions:
- Open an issue in the GitHub repository
- Check existing issues for solutions
- Review API documentation at `/api/v1/docs`

---

**Built with ❤️ using FastAPI, MongoDB, and Docker**
