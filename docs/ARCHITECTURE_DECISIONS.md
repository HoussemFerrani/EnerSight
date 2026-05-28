> ⚠️ **PARTIALLY OUTDATED** — These ADRs were written when the time-series store was InfluxDB and deployment used Docker. Both have since changed: InfluxDB was replaced by **Supabase Postgres** with `pg_partman` monthly partitioning (see [README.md → Time-Series Storage](../README.md#time-series-storage)), and Docker was dropped in favor of native Render deployment. The clean-architecture, dependency-injection, and async-first decisions described here remain accurate.

---

# Architecture Decision Records (ADR)

## ADR-001: Clean Architecture Implementation

**Status:** Accepted  
**Date:** 2026-02-14  
**Context:** Building an academic-level, enterprise-grade energy monitoring platform

### Decision

Implement **Clean Architecture** (Onion Architecture) with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│           Presentation Layer (API)          │
│         FastAPI Routes & Controllers        │
├─────────────────────────────────────────────┤
│           Service Layer (Business Logic)    │
│    Energy Service, Prediction Service, etc  │
├─────────────────────────────────────────────┤
│         Repository Layer (Data Access)      │
│    Energy Repository, User Repository       │
├─────────────────────────────────────────────┤
│             Infrastructure Layer            │
│   Database, MQTT, ML Models, External APIs  │
└─────────────────────────────────────────────┘
```

**Principles:**
1. **Dependency Inversion**: Inner layers don't depend on outer layers
2. **Single Responsibility**: Each layer has one reason to change
3. **Testability**: Easy to mock dependencies and test in isolation
4. **Maintainability**: Changes in one layer don't affect others

### Consequences

**Positive:**
- ✅ Highly testable with clean dependency injection
- ✅ Easy to swap implementations (e.g., change database)
- ✅ Clear separation facilitates team collaboration
- ✅ Scalable architecture for future growth

**Negative:**
- ⚠️ More boilerplate code initially
- ⚠️ Learning curve for developers unfamiliar with pattern

---

## ADR-002: Repository Pattern for Data Access

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Use **Repository Pattern** to abstract data access logic:

- `BaseRepository` provides generic CRUD operations
- Concrete repositories implement domain-specific queries
- Enables swapping data sources without changing business logic

**Example:**
```python
class EnergyDataRepository(TimeSeriesRepository):
    async def write_measurement(...)
    async def query_range(...)
    async def aggregate(...)
```

### Rationale

1. **Abstraction**: Business logic doesn't know about InfluxDB/PostgreSQL
2. **Testing**: Easy to create mock repositories for unit tests
3. **Consistency**: Standardized data access patterns
4. **Flexibility**: Can switch databases without rewriting services

### Alternatives Considered

- **Direct database access**: Rejected (tight coupling, hard to test)
- **DAO pattern**: Similar, but Repository is more domain-focused

---

## ADR-003: Pydantic Settings for Configuration

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Use **Pydantic Settings** for type-safe configuration management:

```python
class Settings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    postgres_url: str
    ...
```

### Benefits

1. **Type Safety**: Automatic validation of environment variables
2. **IDE Support**: Autocomplete and type checking
3. **Documentation**: Self-documenting configuration
4. **12-Factor App**: Environment-based configuration
5. **Validation**: Built-in validators for complex rules

### Implementation

- Settings loaded from `.env` file
- Singleton pattern via `@lru_cache()`
- Different configs for dev/staging/production

---

## ADR-004: Structured Logging with JSON

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Implement **structured logging** with JSON format for production:

```python
logger.info(
    "Energy reading recorded",
    extra={
        "device_id": "sensor_001",
        "consumption": 1250.5,
        "location": "Lab A",
    }
)
```

### Rationale

1. **Machine Parseable**: Easy integration with log aggregation tools
2. **Contextual**: Rich metadata for debugging
3. **Searchable**: Query logs by specific fields
4. **Standards**: Industry best practice for microservices

### Production Stack

- **Development**: Colored console logs
- **Production**: JSON logs → Logstash → Elasticsearch → Kibana (ELK)

---

## ADR-005: Custom Exception Hierarchy

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Create domain-specific exception hierarchy:

```python
EnerSightException (base)
├── APIException
│   ├── ValidationError
│   ├── AuthenticationError
│   └── ResourceNotFoundError
├── DatabaseException
├── MLException
└── IoTException
```

### Benefits

1. **Type Safety**: Catch specific exception types
2. **Error Context**: Exceptions carry error codes and details
3. **HTTP Mapping**: Auto-map to correct status codes
4. **Client-Friendly**: Consistent error response format

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Temperature out of valid range",
    "type": "ValidationError",
    "details": {
      "field": "temperature",
      "value": 100.0
    }
  }
}
```

---

## ADR-006: Dependency Injection Container

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Implement **Dependency Injection** for managing application dependencies:

```python
@app.get("/energy")
async def get_energy(
    db: AsyncSession = Depends(get_postgres_session),
    influx: InfluxDBClient = Depends(get_influxdb_client),
):
    ...
```

### Benefits

1. **Testability**: Easy to inject mocks for testing
2. **Lifecycle Management**: Automatic resource cleanup
3. **Loose Coupling**: Components don't create their own dependencies
4. **Configuration**: Centralized dependency configuration

### Lifecycle Management

- **Startup**: Initialize database pools, load ML models
- **Request**: Create sessions, inject dependencies
- **Shutdown**: Close connections, cleanup resources

---

## ADR-007: Service Layer Pattern

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Introduce **Service Layer** between API and Repository:

```
API Routes → Services → Repositories → Database
```

### Responsibilities

**Service Layer:**
- Business logic and validation
- Transaction orchestration
- ML model integration
- Complex queries across repositories

**Benefits:**
- Reusable business operations
- Keep controllers thin
- Centralized validation
- Easy unit testing

---

## ADR-008: Async/Await for I/O Operations

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Use **async/await** for all I/O-bound operations:

```python
async def get_energy_data(...) -> List[dict]:
    data = await repository.query_range(...)
    return data
```

### Rationale

1. **Performance**: Handle thousands of concurrent requests
2. **Scalability**: Non-blocking I/O for database queries
3. **Modern**: FastAPI's native async support
4. **Efficient**: Better resource utilization

### Database Support

- **PostgreSQL**: `asyncpg` driver
- **InfluxDB**: Async client
- **Redis**: `aioredis` for caching

---

## ADR-009: Testing Strategy - Pyramid Approach

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Follow **Testing Pyramid**:

```
            ┌─────┐
           │ E2E  │        Few, slow, expensive
          ├───────┤
         │ Integration│     Medium coverage
        ├───────────┤
       │  Unit Tests  │   Many, fast, cheap
      └───────────────┘
```

### Implementation

1. **Unit Tests**: Service layer logic (70%)
   - Mock all dependencies
   - Fast execution (< 1s total)
   - High coverage (>80%)

2. **Integration Tests**: API endpoints (25%)
   - Test real API calls
   - Mock external services
   - Database in-memory

3. **E2E Tests**: Critical user flows (5%)
   - Full stack testing
   - Slow but comprehensive

### Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **httpx**: Async HTTP client for API tests

---

## ADR-010: API Versioning Strategy

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

Use **URL path versioning**:

```
/api/v1/energy
/api/v2/energy
```

### Rationale

1. **Clarity**: Version immediately visible in URL
2. **Backward Compatibility**: Old versions remain accessible
3. **Client Control**: Clients choose when to upgrade
4. **Standard**: REST API best practice

### Version Lifecycle

- **v1**: Current, maintenance mode eventually
- **v2**: Future with breaking changes
- **Deprecation**: 6-month notice before removal

---

## ADR-011: ML Model Loading Strategy

**Status:** Accepted  
**Date:** 2026-02-14

### Decision

**Lazy loading** with **caching** for ML models:

```python
class ModelRegistry:
    def get_model(self, model_name: str):
        if not loaded:
            model = load_model()  # Load on first access
            cache[model_name] = model
        return cache[model_name]
```

### Benefits

1. **Fast Startup**: Don't load all models at once
2. **Memory Efficient**: Only load models in use
3. **Hot Reload**: Reload models without restart
4. **Scalability**: Support many models

### Alternatives

- **Eager Loading**: All models at startup (slow, memory intensive)
- **No Caching**: Reload every request (very slow)

---

## Summary: Architecture Principles

### SOLID Principles

✅ **S** - Single Responsibility: Each class has one job  
✅ **O** - Open/Closed: Open for extension, closed for modification  
✅ **L** - Liskov Substitution: Interfaces are substitutable  
✅ **I** - Interface Segregation: Small, focused interfaces  
✅ **D** - Dependency Inversion: Depend on abstractions  

### Design Patterns Used

1. **Repository Pattern** - Data access abstraction
2. **Service Layer** - Business logic orchestration
3. **Dependency Injection** - Loose coupling
4. **Factory Pattern** - Object creation
5. **Singleton Pattern** - Shared configuration
6. **Unit of Work** - Transaction management

### Best Practices

- ✅ Type hints everywhere (Python 3.11+)
- ✅ Async/await for I/O operations
- ✅ Structured logging with context
- ✅ Comprehensive error handling
- ✅ Environment-based configuration
- ✅ Automated testing (unit + integration)
- ✅ API documentation (OpenAPI/Swagger)
- ✅ Code quality tools (black, flake8, mypy)

---

**For academic submission**, these ADRs demonstrate:
- Understanding of software architecture
- Application of design patterns
- Engineering best practices
- Professional development methodology
