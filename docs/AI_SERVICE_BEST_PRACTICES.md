# AI Service Configuration Best Practices

This document outlines the improved configuration approach for AI services in the Genascope backend.

## Overview

The application now follows a **fail-fast approach** for production environments while maintaining flexibility for development and testing.

## Key Principles

### 1. Environment-Specific Behavior

- **Development**: Mock mode allowed when OpenAI is not configured
- **Staging**: Real services required, fail fast if unavailable  
- **Production**: Strict validation, no mock mode, fail fast on startup

### 2. Fail-Fast Philosophy

In production environments:
- Missing configuration causes immediate startup failure
- Service validation occurs during startup
- No silent degradation to mock mode
- Clear error messages for troubleshooting

### 3. Circuit Breaker Protection

- Implements circuit breaker pattern for external AI services
- Graceful degradation with user-friendly error messages
- Automatic recovery attempts after timeout
- Configurable failure thresholds per environment

## Configuration

### Environment Variables

```bash
# Required in production
OPENAI_API_KEY=sk-...
ENVIRONMENT=production

# Optional configuration
FAIL_FAST_ON_STARTUP=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60
```

### Environment-Specific Recommendations

#### Production
```bash
ENVIRONMENT=production
FAIL_FAST_ON_STARTUP=true
ANONYMIZE_BEFORE_AI=true
ENABLE_AUDIT_LOGGING=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=3
```

#### Development
```bash
ENVIRONMENT=development
FAIL_FAST_ON_STARTUP=false
ANONYMIZE_BEFORE_AI=false
ENABLE_AUDIT_LOGGING=false
CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
```

## Error Handling

### Startup Errors

The application will fail to start in these scenarios:

1. **Production without OpenAI key**
   ```
   RuntimeError: Missing required OpenAI configuration
   ```

2. **Invalid production configuration**
   ```
   RuntimeError: Invalid production configuration: Mock mode not allowed
   ```

3. **OpenAI connection failure** (when fail_fast_on_startup=true)
   ```
   RuntimeError: OpenAI connection validation failed
   ```

### Runtime Errors

When AI services are unavailable:

1. **Circuit breaker open**
   ```
   HTTP 503: Service temporarily unavailable. Please try again later.
   ```

2. **Service degradation**
   - Clear error messages to users
   - No silent fallback to mock responses
   - Proper HTTP status codes

## Benefits

### Reliability
- No unexpected behavior differences between environments
- Clear failure modes with actionable error messages
- Prevents silent data corruption from mock responses

### Debugging
- Environment-specific logging levels
- Configuration validation at startup
- Clear separation between real and mock behavior

### Security
- No accidental exposure of mock data in production
- Consistent data handling across environments
- Audit logging in production environments

## Migration Guide

### From Mock Fallback to Fail-Fast

1. **Update environment configuration**
   ```bash
   # Old approach - silent fallback
   OPENAI_API_KEY=  # Empty allowed
   
   # New approach - explicit configuration
   ENVIRONMENT=production
   OPENAI_API_KEY=sk-actual-key-required
   ```

2. **Handle startup failures**
   ```python
   # Application will now fail fast with clear error messages
   # No need to check for mock mode at runtime
   ```

3. **Update error handling**
   ```python
   # Replace mock fallbacks with proper error responses
   try:
       result = await ai_service.process(data)
   except HTTPException as e:
       # Return user-friendly error message
       return {"error": "AI service temporarily unavailable"}
   ```

## Testing

### Unit Tests
- Mock services using proper test frameworks
- Environment variable injection for different scenarios
- Circuit breaker state testing

### Integration Tests
- Test startup failure scenarios
- Validate production configuration checks
- Test service degradation handling

### End-to-End Tests
- Test with real AI services in staging
- Validate error handling flows
- Performance testing with circuit breakers
