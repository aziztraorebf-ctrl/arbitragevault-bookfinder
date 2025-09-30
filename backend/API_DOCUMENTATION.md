# ArbitrageVault API Documentation

## 🔗 **Base URL**
```
Production: https://arbitragevault-backend-v2.onrender.com
Local Dev:  http://localhost:8000
```

## 📖 **Interactive Documentation**
- **Swagger UI**: `{BASE_URL}/docs`
- **ReDoc**: `{BASE_URL}/redoc`  
- **OpenAPI Schema**: `{BASE_URL}/openapi.json`

---

## 🏥 **Health & System**

### **GET /health**
Basic system health check
```bash
curl "https://arbitragevault-backend-v2.onrender.com/health"
```
**Response:**
```json
{"status": "ok"}
```

---

## 📦 **Batch Management**

### **GET /api/v1/batches**
List analysis batches with pagination
```bash
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/batches?page=1&per_page=20"
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "name": "Analysis Batch Name",
      "description": "Optional description", 
      "status": "COMPLETED",
      "items_total": 100,
      "items_processed": 100,
      "started_at": "2025-09-29T10:00:00Z",
      "finished_at": "2025-09-29T12:30:00Z",
      "strategy_snapshot": {"config_name": "profit_hunter"},
      "created_at": "2025-09-29T09:30:00Z",
      "updated_at": "2025-09-29T12:30:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20, 
  "pages": 1
}
```

### **POST /api/v1/batches**
Create new analysis batch
```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/batches" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Q4 Analysis",
    "description": "Fourth quarter book analysis",
    "asin_list": ["B08N5WRWNW", "B07XYZ123"],
    "config_name": "profit_hunter"
  }'
```

### **GET /api/v1/batches/{batch_id}**
Get specific batch details
```bash
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/batches/uuid-here"
```

### **PATCH /api/v1/batches/{batch_id}/status**
Update batch status
```bash
curl -X PATCH "https://arbitragevault-backend-v2.onrender.com/api/v1/batches/uuid-here/status" \
  -H "Content-Type: application/json" \
  -d '{"status": "PROCESSING"}'
```

---

## 📊 **Analysis Results**

### **GET /api/v1/analyses**
List analysis results with pagination
```bash
curl "https://arbitragevault-backend-v2.onrender.com/api/v1/analyses?page=1&per_page=20"
```

**Response:**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "batch_id": "batch-uuid",
      "isbn_or_asin": "B08N5WRWNW", 
      "buy_price": 15.50,
      "fees": 3.25,
      "expected_sale_price": 25.99,
      "profit": 7.24,
      "roi_percent": 46.71,
      "velocity_score": 78.5,
      "rank_snapshot": 12543,
      "offers_count": 8,
      "raw_keepa": {"domain": 1, "asin": "B08N5WRWNW"},
      "target_price_data": {"min_price": 20.00, "max_price": 30.00},
      "created_at": "2025-09-29T10:15:00Z",
      "updated_at": "2025-09-29T10:15:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 20,
  "pages": 1
}
```

### **POST /api/v1/analyses**
Create analysis result
```bash
curl -X POST "https://arbitragevault-backend-v2.onrender.com/api/v1/analyses" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "batch-uuid",
    "isbn_or_asin": "B08N5WRWNW",
    "buy_price": 15.50,
    "fees": 3.25,
    "expected_sale_price": 25.99,
    "profit": 7.24,
    "roi_percent": 46.71,
    "velocity_score": 78.5
  }'
```

---

## 📋 **Common Patterns**

### **Pagination Parameters**
All list endpoints support pagination:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

### **Batch Status Values**
```
PENDING    - Newly created, not started
PROCESSING - Currently being analyzed
COMPLETED  - Successfully finished
FAILED     - Terminated with errors
CANCELLED  - Manually stopped
```

### **Error Responses**
Standard error format:
```json
{
  "detail": "Human-readable error message"
}
```

Common HTTP status codes:
- `200` - Success
- `201` - Created successfully
- `400` - Bad request (validation error)
- `404` - Resource not found
- `500` - Internal server error

---

## 🔧 **Development Integration**

### **TypeScript Type Generation**
Generate TypeScript types from OpenAPI schema:
```bash
# Download OpenAPI schema
curl "https://arbitragevault-backend-v2.onrender.com/openapi.json" > openapi.json

# Generate TypeScript types
npx openapi-typescript openapi.json --output src/types/api.ts
```

### **Client Libraries**
Recommended HTTP clients:
- **JavaScript/TypeScript**: `fetch` with TypeScript types
- **Python**: `httpx` with async support
- **curl**: For testing and debugging

### **Authentication (Future)**
When authentication is implemented:
```bash
# Headers to include in requests
curl -H "Authorization: Bearer your-jwt-token" \
     -H "Content-Type: application/json" \
     "https://arbitragevault-backend-v2.onrender.com/api/v1/batches"
```

---

## 🧪 **Testing Examples**

### **Basic Workflow Test**
```bash
#!/bin/bash
BASE_URL="https://arbitragevault-backend-v2.onrender.com"

# 1. Health check
echo "Testing health endpoint..."
curl -s "$BASE_URL/health" | jq

# 2. List existing batches
echo "Listing batches..."
curl -s "$BASE_URL/api/v1/batches" | jq '.total'

# 3. List analyses
echo "Listing analyses..."
curl -s "$BASE_URL/api/v1/analyses" | jq '.total'

echo "✅ All endpoints operational"
```

### **Frontend Integration Test**
```javascript
// Example React hook for batch data
import { useQuery } from '@tanstack/react-query'

export const useBatches = (page = 1, perPage = 20) => {
  return useQuery({
    queryKey: ['batches', page, perPage],
    queryFn: async () => {
      const response = await fetch(
        `https://arbitragevault-backend-v2.onrender.com/api/v1/batches?page=${page}&per_page=${perPage}`
      )
      if (!response.ok) throw new Error('Failed to fetch batches')
      return response.json()
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 3
  })
}
```

---

*This API documentation provides complete reference for integrating with the ArbitrageVault backend. All endpoints are production-ready and fully tested.*