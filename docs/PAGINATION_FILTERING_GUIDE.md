# Chat Configuration API - Pagination & Filtering Quick Reference

## Strategy Endpoints

### List Strategies with Pagination
```bash
# Basic pagination
curl "http://localhost:8000/api/v1/chat-configuration/strategies?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter active strategies only
curl "http://localhost:8000/api/v1/chat-configuration/strategies?active_only=true" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Combined: Active strategies with pagination
curl "http://localhost:8000/api/v1/chat-configuration/strategies?active_only=true&skip=0&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Strategy Parameters
- **skip**: Number of records to skip (default: 0)
- **limit**: Maximum records to return (default: 100)
- **active_only**: Filter by active status (default: false)

## Knowledge Source Endpoints

### List Knowledge Sources with Filtering
```bash
# Basic pagination
curl "http://localhost:8000/api/v1/chat-configuration/knowledge-sources?skip=0&limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by source type
curl "http://localhost:8000/api/v1/chat-configuration/knowledge-sources?source_type=guideline" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Filter by processing status
curl "http://localhost:8000/api/v1/chat-configuration/knowledge-sources?processing_status=pending" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Combined filters
curl "http://localhost:8000/api/v1/chat-configuration/knowledge-sources?source_type=research_paper&processing_status=completed&limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Knowledge Source Parameters
- **skip**: Number of records to skip (default: 0)
- **limit**: Maximum records to return (default: 100)
- **source_type**: Filter by source type
  - `direct`
  - `guideline`
  - `research_paper`
  - `protocol`
  - `risk_model`
  - `custom_document`
  - `custom_link`
- **processing_status**: Filter by processing status
  - `pending`
  - `processing`
  - `completed`
  - `failed`
  - `retry`

## Response Format

### Paginated Strategy Response
```json
[
  {
    "id": "uuid-string",
    "name": "Strategy Name",
    "description": "Strategy description",
    "goal": "Strategy goal",
    "specialty": "Oncology",
    "is_active": true,
    "created_at": "2025-06-20T12:00:00Z",
    "updated_at": "2025-06-20T12:00:00Z",
    "knowledge_sources": [],
    "targeting_rules": [],
    "outcome_actions": []
  }
]
```

### Paginated Knowledge Source Response
```json
[
  {
    "id": "uuid-string",
    "name": "Knowledge Source Name",
    "source_type": "guideline",
    "description": "Source description",
    "processing_status": "completed",
    "content_type": "application/pdf",
    "is_active": true,
    "created_at": "2025-06-20T12:00:00Z",
    "updated_at": "2025-06-20T12:00:00Z"
  }
]
```

## Best Practices

### Pagination
1. **Use reasonable page sizes**: Limit values between 10-100 are recommended
2. **Implement client-side pagination**: Use skip/limit for page navigation
3. **Handle empty results**: Check if response array is empty to detect end of data

### Filtering
1. **Combine filters judiciously**: Multiple filters are AND'ed together
2. **Handle invalid filter values**: API returns empty results for invalid enum values
3. **Case sensitivity**: Filter values are case-sensitive for enum types

### Performance
1. **Cache filter results**: Consider caching frequently used filter combinations
2. **Use active_only filter**: When only active strategies are needed
3. **Limit large queries**: Use smaller page sizes for better response times

## Testing Examples

### Test Basic Pagination
```bash
# Page 1 (first 5 records)
curl "http://localhost:8000/api/v1/chat-configuration/strategies?skip=0&limit=5"

# Page 2 (next 5 records)
curl "http://localhost:8000/api/v1/chat-configuration/strategies?skip=5&limit=5"

# Page 3 (next 5 records)
curl "http://localhost:8000/api/v1/chat-configuration/strategies?skip=10&limit=5"
```

### Test Filter Combinations
```bash
# Active strategies only
curl "http://localhost:8000/api/v1/chat-configuration/strategies?active_only=true"

# Completed guidelines only
curl "http://localhost:8000/api/v1/chat-configuration/knowledge-sources?source_type=guideline&processing_status=completed"

# First 3 pending direct sources
curl "http://localhost:8000/api/v1/chat-configuration/knowledge-sources?source_type=direct&processing_status=pending&limit=3"
```

## Error Handling

### Common Issues
1. **Invalid enum values**: Returns 422 for invalid processing_status or source_type
2. **Large skip values**: Returns empty array if skip exceeds total records
3. **Zero limit**: Returns empty array (valid behavior)
4. **Missing authentication**: Returns 401 if Authorization header is missing

### Error Response Format
```json
{
  "detail": "Validation error message or specific error description"
}
```

## Integration with E2E Tests

The E2E test suite validates all these pagination and filtering scenarios:
- Basic pagination functionality
- Filter-only requests
- Combined filter and pagination requests
- Edge cases (large skip, zero limit, invalid values)
- Result consistency across multiple requests
- Performance with larger datasets

Run the comprehensive tests:
```bash
./run_chat_config_e2e_tests.sh
```

Run specific pagination tests:
```bash
python -m pytest app/tests/e2e/api/test_chat_configuration_e2e.py::TestChatConfigurationE2E::test_pagination_and_filtering -v
```
