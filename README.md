# Inventory Microservice 

A production-ready FastAPI microservice for managing e-commerce inventory with MongoDB, featuring automated CI/CD deployment to DigitalOcean.

## 🚀 Features

- **RESTful API** with versioning (`/api/v1`)
- **Async/Await** operations for high performance
- **MongoDB** with Motor (async driver) and connection pooling
- **Stock Management**: Create, update, and adjust inventory quantities
- **Audit Trail**: Complete stock movement history
- **Pagination**: Efficient data retrieval with configurable limits
- **Docker Support**: Multi-stage builds with health checks
- **Automated CI/CD**: Test, build, and deploy on every push
- **Comprehensive Tests**: 16 tests with 78%+ coverage
- **Production-Ready**: Exception handling, logging, CORS, security

## 🌐 Live API

**Base URL**: http://68.183.227.95:8001

- **API Docs**: http://68.183.227.95:8001/api/v1/docs
- **Health Check**: http://68.183.227.95:8001/api/v1/health

## 📋 Tech Stack

- **Backend**: FastAPI 0.115.0, Python 3.11
- **Database**: MongoDB 7.0
- **Web Server**: Uvicorn (ASGI)
- **Testing**: Pytest, pytest-asyncio, pytest-cov
- **Linting**: Ruff
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Deployment**: DigitalOcean Droplet

## 🛠️ Local Development

### Prerequisites

- Python 3.11+
- MongoDB 7.0+
- Docker & Docker Compose (optional)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Soksothy/Devop02.git
   cd Devop02/inventory-service
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start MongoDB and Application**
   
   **Option A: Using Docker Compose (Recommended)**
   ```bash
   docker-compose up -d
   ```
   
   **Option B: Manual Setup**
   ```bash
   # Start MongoDB
   docker run -d -p 27017:27017 --name mongodb mongo:7.0
   
   # Run the application
   python -m uvicorn app.main:app --reload --port 8001
   ```

5. **Access the API**
   - **Swagger UI**: http://localhost:8001/api/v1/docs
   - **ReDoc**: http://localhost:8001/api/v1/redoc
   - **Health Check**: http://localhost:8001/api/v1/health

## 📚 API Documentation

### Available Endpoints

#### Health Check
```http
GET /api/v1/health
```
Check service and database connectivity.

#### List Inventory Items
```http
GET /api/v1/inventory/items?page=1&limit=20&product_id=PROD-001
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `limit` (int): Items per page (default: 20, max: 100)
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
      "created_at": "2025-12-25T14:00:00",
      "updated_at": "2025-12-25T14:00:00"
    }
  ]
}
```

#### Get Single Inventory Item
```http
GET /api/v1/inventory/items/{product_id}
```

#### Create Inventory Item
```http
POST /api/v1/inventory/items
Content-Type: application/json

{
  "product_id": "PROD-002",
  "quantity": 50,
  "warehouse_location": "WH-B1"
}
```

#### Update Inventory Item
```http
PUT /api/v1/inventory/items/{product_id}
Content-Type: application/json

{
  "quantity": 75,
  "warehouse_location": "WH-A2"
}
```

#### Adjust Stock (Add/Subtract)
```http
POST /api/v1/inventory/items/{product_id}/adjust
Content-Type: application/json

{
  "quantity": -10,
  "reason": "Sold 10 units"
}
```
- Use **positive** values to add stock
- Use **negative** values to subtract stock

#### Check Stock Availability (For Order Service)
```http
POST /api/v1/inventory/check-availability
Content-Type: application/json

{
  "product_id": "PROD-001",
  "required_quantity": 10
}
```

**Response:**
```json
{
  "product_id": "PROD-001",
  "available": true,
  "current_quantity": 100,
  "required_quantity": 10,
  "warehouse_location": "WH-A1"
}
```

#### Bulk Check Stock Availability
```http
POST /api/v1/inventory/check-availability/bulk
Content-Type: application/json

{
  "items": [
    {
      "product_id": "PROD-001",
      "required_quantity": 5
    },
    {
      "product_id": "PROD-002",
      "required_quantity": 10
    }
  ]
}
```

**Response:**
```json
{
  "all_available": true,
  "items": [
    {
      "product_id": "PROD-001",
      "available": true,
      "current_quantity": 100,
      "required_quantity": 5,
      "warehouse_location": "WH-A1"
    },
    {
      "product_id": "PROD-002",
      "available": true,
      "current_quantity": 50,
      "required_quantity": 10,
      "warehouse_location": "WH-B1"
    }
  ]
}
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test
pytest tests/test_inventory.py::TestHealthEndpoint -v

# Run with detailed output
pytest tests/ -vv
```

### Test Coverage
- **16 tests** covering all endpoints
- **78%+ code coverage**
- Async testing with mocked MongoDB

## 🚀 CI/CD Pipeline

### Automated Workflow

Every push to `main` triggers:

1. **Test & Lint**
   - Run pytest with coverage
   - Lint code with Ruff

2. **Build & Push**
   - Build Docker image
   - Push to Docker Hub: `soksothy/inventory-service:latest`

3. **Deploy to DigitalOcean**
   - SSH into droplet
   - Pull latest image
   - Restart containers
   - Run health check

### GitHub Secrets Required

Add these secrets in **Settings → Secrets and variables → Actions**:

- `DOCKER_USERNAME`: Docker Hub username
- `DOCKER_PASSWORD`: Docker Hub password/token
- `DO_HOST`: DigitalOcean droplet IP
- `DO_PASSWORD`: Server root password

## 🌐 Production Deployment

### Manual Deployment to DigitalOcean

1. **SSH into your server**
   ```bash
   ssh root@68.183.227.95
   ```

2. **Create Docker network**
   ```bash
   docker network create inventory-network
   ```

3. **Start MongoDB**
   ```bash
   docker run -d \
     --name inventory-mongodb \
     --network inventory-network \
     --restart unless-stopped \
     -p 27017:27017 \
     -v mongodb_data:/data/db \
     -e MONGO_INITDB_DATABASE=inventory_db \
     mongo:7.0
   ```

4. **Start API Service**
   ```bash
   docker run -d \
     --name inventory-api \
     --network inventory-network \
     --restart unless-stopped \
     -p 8001:8001 \
     -e MONGODB_URI=mongodb://inventory-mongodb:27017 \
     -e DATABASE_NAME=inventory_db \
     -e PORT=8001 \
     -e ENVIRONMENT=production \
     soksothy/inventory-service:latest
   ```

5. **Verify Deployment**
   ```bash
   docker ps
   docker logs inventory-api
   curl http://localhost:8001/api/v1/health
   ```

## 📁 Project Structure

```
inventory-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app & startup
│   ├── config.py            # Configuration settings
│   ├── database.py          # MongoDB connection
│   ├── schemas.py           # Pydantic models
│   ├── observability.py     # Metrics, logging & tracing
│   ├── models/
│   │   ├── __init__.py
│   │   └── inventory.py     # Business logic
│   └── routers/
│       ├── __init__.py
│       └── inventory.py     # API endpoints
├── tests/
│   ├── __init__.py
│   └── test_inventory.py    # Test suite (16 tests, 78%+ coverage)
├── .github/
│   └── workflows/
│       └── ci-cd.yml        # GitHub Actions CI/CD pipeline
├── Dockerfile                      # Multi-stage production build
├── docker-compose.yml              # Local development stack
├── docker-compose.observability.yml # Full monitoring stack (Prometheus + Grafana)
├── prometheus.yml                  # Prometheus scrape configuration
├── grafana-datasources.yml         # Grafana datasource config
├── requirements.txt                # Python dependencies
├── Inventory_API.postman_collection.json  # Postman collection
├── POSTMAN_GUIDE.md               # Postman usage guide
└── README.md                      # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `DATABASE_NAME` | `inventory_db` | Database name |
| `PORT` | `8001` | API server port |
| `ENVIRONMENT` | `development` | Environment mode |
| `API_V1_PREFIX` | `/api/v1` | API version prefix |
| `DEFAULT_PAGE_SIZE` | `20` | Default pagination size |
| `MAX_PAGE_SIZE` | `100` | Maximum pagination size |

## 🛡️ Security Features

- ✅ Non-root Docker container
- ✅ CORS configuration
- ✅ Input validation with Pydantic
- ✅ Error handling and logging
- ✅ Health checks
- ✅ Read-only file system

## 🐛 Troubleshooting

### Common Issues

**Issue**: `Cannot connect to MongoDB`
```bash
# Check MongoDB is running
docker ps | grep mongodb

# Check logs
docker logs inventory-mongodb

# Test connection
docker exec -it inventory-mongodb mongosh
```

**Issue**: `Port 8001 already in use`
```bash
# Find process using port
netstat -ano | findstr :8001  # Windows
lsof -i :8001                  # Linux/Mac

# Kill the process or change port
PORT=8002 python -m uvicorn app.main:app --port 8002
```

**Issue**: `Tests failing`
```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest tests/ -vv
```

## 📊 Monitoring

### Check Application Logs
```bash
# Docker logs
docker logs inventory-api -f

# Specific number of lines
docker logs inventory-api --tail 100
```

### Monitor Container Health
```bash
# Container status
docker ps

# Resource usage
docker stats inventory-api

# Health check
curl http://68.183.227.95:8001/api/v1/health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is for educational purposes.

## 👨‍💻 Author

**Soksothy**
- GitHub: [@Soksothy](https://github.com/Soksothy)
- Docker Hub: [soksothy](https://hub.docker.com/u/soksothy)

---

**⭐ Star this repo if you find it useful!**
   
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

## � Observability & Monitoring

The Inventory Service includes a comprehensive observability stack for production monitoring.

### Features

- **Prometheus Metrics**: Real-time performance metrics exported at `/metrics`
- **Structured JSON Logging**: Machine-readable logs for log aggregation
- **Request Tracing**: Correlation IDs for tracking requests across services
- **Health Checks**: Liveness and readiness probes for Kubernetes
- **Grafana Dashboards**: Pre-configured visualization (optional)

### Quick Start - Observability Stack

Run the full stack with Prometheus and Grafana:

```bash
cd inventory-service
docker-compose -f docker-compose.observability.yml up -d
```

**Access Points:**
- API: http://localhost:8001
- API Docs: http://localhost:8001/api/v1/docs
- Metrics: http://localhost:8001/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Available Metrics

The service exposes the following Prometheus metrics:

| Metric | Type | Description |
|--------|------|-------------|
| `inventory_requests_total` | Counter | Total HTTP requests by method, endpoint, and status |
| `inventory_request_duration_seconds` | Histogram | Request latency distribution |
| `inventory_active_requests` | Gauge | Currently active requests |
| `inventory_db_operations_total` | Counter | Database operations by type |
| `inventory_db_operation_duration_seconds` | Histogram | Database operation latency |
| `inventory_total_items` | Gauge | Total inventory items in database |
| `inventory_total_stock_quantity` | Gauge | Total stock quantity across all items |
| `inventory_low_stock_items` | Gauge | Items with stock below threshold |

### Health Check Endpoints

**Liveness Probe** - Check if service is running
```bash
curl http://localhost:8001/health/live
# Response: {"status": "alive"}
```

**Readiness Probe** - Check if service is ready (DB connected)
```bash
curl http://localhost:8001/health/ready
# Response: {"status": "ready", "database": "connected"}
```

### Structured Logging

All logs are output in JSON format for easy parsing by log aggregators (ELK, Splunk, etc.):

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "level": "INFO",
  "message": "Request completed",
  "trace_id": "abc123...",
  "method": "POST",
  "path": "/api/v1/inventory",
  "status_code": 201,
  "duration_ms": 45.67
}
```

### Request Tracing

Every request receives a unique `X-Trace-Id` header that appears in:
- Response headers
- All log entries for that request
- Error responses

Use trace IDs to track requests across services and correlate logs.

### Grafana Dashboard Setup

1. **Access Grafana**: http://localhost:3000 (admin/admin)
2. **Prometheus is pre-configured** as a datasource
3. **Create a dashboard** with these queries:

**Request Rate:**
```promql
rate(inventory_requests_total[5m])
```

**95th Percentile Latency:**
```promql
histogram_quantile(0.95, rate(inventory_request_duration_seconds_bucket[5m]))
```

**Active Requests:**
```promql
inventory_active_requests
```

**Database Operation Rate:**
```promql
rate(inventory_db_operations_total[5m])
```

**Low Stock Items:**
```promql
inventory_low_stock_items
```

### Production Monitoring

For production deployments:

1. **Deploy Prometheus** to scrape `/metrics` endpoint
2. **Configure Grafana** to visualize metrics
3. **Set up alerts** for:
   - High error rates (5xx responses)
   - High latency (p95 > threshold)
   - Database connection failures
   - Low stock items above threshold

4. **Aggregate logs** to a centralized logging system
5. **Use trace IDs** to debug cross-service issues

### Example Prometheus Configuration

```yaml
scrape_configs:
  - job_name: 'inventory-service'
    scrape_interval: 10s
    static_configs:
      - targets: ['68.183.227.95:8001']
    metrics_path: '/metrics'
```

## �📞 Support

For issues and questions:
- Open an issue in the GitHub repository
- Check existing issues for solutions
- Review API documentation at `/api/v1/docs`

---

**Built with ❤️ using FastAPI, MongoDB, and Docker**
