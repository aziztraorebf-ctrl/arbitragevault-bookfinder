# 🎫 FOLLOW-UP TICKETS - Post v1.4.0

## 🚨 **HIGH PRIORITY - Business Logic Fixes**

### **TICKET #001: Fix Calculation Type Conversion Error**
**Status**: `bug` `high-priority` `business-logic`
**Assignee**: TBD  
**Estimate**: 2-3 hours

**Description**:
The analyze_product() function fails with type conversion error when processing Keepa data.

**Error Message**:
```
Analysis failed for B00FLIJJSA: can't multiply sequence by non-int of type 'float'
```

**Location**: 
- File: `backend/app/api/v1/routers/keepa.py`
- Function: `analyze_product()`
- Lines: ~150-160

**Root Cause**:
Mixed types between parsed_data (strings/None) and Decimal calculations. The line:
```python
estimated_cost = Decimal(str(parsed_data.get('current_price', 20.0))) * Decimal('0.75')
```

**Expected Fix**:
- Add robust type checking and conversion
- Handle missing/None values gracefully  
- Ensure all price calculations use consistent Decimal types
- Add fallback values for missing Keepa data

**Acceptance Criteria**:
- [ ] All calculations complete without type errors
- [ ] Recommendations return BUY/WATCH/PASS instead of ERROR
- [ ] Smoke test shows analysis with valid ROI/velocity scores
- [ ] Edge cases (missing price data) handled gracefully

---

### **TICKET #002: Fix Parser Null Check Errors**
**Status**: `bug` `high-priority` `data-processing`
**Assignee**: TBD  
**Estimate**: 1-2 hours

**Description**:
The Keepa parser fails when processing products with incomplete data.

**Error Message**:
```
Failed to parse Keepa product data: object of type 'NoneType' has no len()
```

**Location**:
- File: `backend/app/services/keepa_parser.py`
- Function: `parse_keepa_product()`

**Root Cause**:
Missing null checks for optional Keepa API fields before processing arrays/objects.

**Expected Fix**:
- Add defensive null checks for all optional fields
- Provide sensible defaults for missing data
- Log warnings for incomplete data without failing
- Ensure parser always returns valid structure

**Acceptance Criteria**:
- [ ] Parser handles products with missing price history
- [ ] Parser handles products with missing BSR data  
- [ ] Parser handles products with missing package dimensions
- [ ] All parsed products have consistent data structure
- [ ] Warnings logged for missing data but processing continues

---

## 🔄 **MEDIUM PRIORITY - Feature Completion**

### **TICKET #003: Implement Async Job Processing**
**Status**: `enhancement` `medium-priority` `scalability`
**Assignee**: TBD  
**Estimate**: 1 day

**Description**:
Complete async job processing for large batches (>100 items) with database persistence.

**Current State**:
Placeholder background task in `process_batch_async()` function.

**Requirements**:
- Job status table (JobStatus model)
- Progress tracking with percentage complete
- Result storage linked to job_id
- Polling endpoint: `GET /api/v1/keepa/jobs/{job_id}`
- Error recovery and retry logic

**Database Schema Needed**:
```sql
CREATE TABLE job_status (
    id UUID PRIMARY KEY,
    batch_id VARCHAR,
    status VARCHAR, -- 'pending', 'running', 'completed', 'failed' 
    total_items INTEGER,
    processed_items INTEGER,
    successful_items INTEGER,
    failed_items INTEGER,
    created_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);
```

**Acceptance Criteria**:
- [ ] Jobs persist across server restarts
- [ ] Progress tracking works in real-time
- [ ] Results accessible after completion
- [ ] Failed jobs can be retried
- [ ] Job cleanup after 7 days

---

### **TICKET #004: Enrich OpenAPI Documentation**
**Status**: `documentation` `medium-priority` `developer-experience`
**Assignee**: TBD  
**Estimate**: 2-3 hours

**Description**:
Add concrete examples to all endpoint schemas for better API documentation.

**Current State**:
Auto-generated schemas without examples.

**Requirements**:
- Example requests/responses for each endpoint
- Error response examples with different codes
- Configuration profile examples  
- Real ASIN examples in documentation

**Files to Update**:
- `backend/app/api/v1/routers/keepa.py` - Add OpenAPI examples
- Consider separate schema files if inline gets too verbose

**Acceptance Criteria**:
- [ ] All endpoints have request examples
- [ ] All endpoints have success response examples
- [ ] All endpoints have error response examples
- [ ] Examples use real ASINs and realistic data
- [ ] Documentation renders correctly in FastAPI /docs

---

## ⚡ **LOW PRIORITY - Optimizations**

### **TICKET #005: Add Performance Monitoring**
**Status**: `enhancement` `low-priority` `observability`
**Assignee**: TBD  
**Estimate**: 2 hours

**Description**:
Track actual API latencies instead of placeholder zeros.

**Current State**:
```python
"average_latency_ms": 0  # TODO: Track latencies
```

**Requirements**:
- Request timing middleware
- Latency percentiles (p50, p90, p95)
- Per-endpoint latency tracking
- Expose in health endpoint

**Implementation Ideas**:
- Use `time.perf_counter()` around API calls
- Moving window average for health endpoint
- Optional: Prometheus metrics integration

**Acceptance Criteria**:
- [ ] Health endpoint shows real latency data
- [ ] Latencies tracked per endpoint type
- [ ] Percentile calculations available
- [ ] Performance data helps identify slow operations

---

### **TICKET #006: Intelligent Cache TTL**
**Status**: `enhancement` `low-priority` `performance`
**Assignee**: TBD  
**Estimate**: 4-6 hours

**Description**:
Dynamic cache TTL based on product characteristics instead of fixed timings.

**Current State**:
- Metadata: 24 hours TTL
- Pricing: 30-60 minutes TTL  
- BSR: 30-60 minutes TTL

**Smart TTL Ideas**:
- High BSR volatility → Shorter cache TTL
- Stable pricing history → Longer cache TTL  
- Popular categories → Shorter TTL
- Rare/OOP books → Longer TTL

**Implementation**:
- Add volatility calculation to parsed data
- Cache entry includes calculated TTL
- Health endpoint shows TTL distribution

**Acceptance Criteria**:
- [ ] Cache TTL varies based on product characteristics
- [ ] High-volatility products update more frequently  
- [ ] Stable products cached longer to save tokens
- [ ] Overall token usage optimized vs data freshness

---

## 📋 **BACKLOG - Future Considerations**

- **Error Alert System**: Slack/email notifications for high error rates
- **Rate Limiting**: Client-side rate limiting for API protection  
- **Batch Size Optimization**: Find optimal batch sizes for Keepa API
- **Data Export Formats**: Additional export formats (JSON, XML)
- **Historical Trends**: Track ROI/velocity changes over time
- **A/B Testing**: Configuration profile performance comparison

---

**📝 Created**: 2025-08-21 Post v1.4.0 release  
**🎯 Focus**: Stabilize business logic, then scale features