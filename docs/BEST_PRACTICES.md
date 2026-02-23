# Best Practices & Coding Standards

> **Academic-Level Software Engineering Guidelines**  
> For the EnerSight Energy Monitoring Platform

---

## 📚 Table of Contents

1. [Code Quality](#code-quality)
2. [Architecture Patterns](#architecture-patterns)
3. [Testing Strategy](#testing-strategy)
4. [Error Handling](#error-handling)
5. [Performance Optimization](#performance-optimization)
6. [Security Best Practices](#security-best-practices)
7. [Documentation](#documentation)
8. [Git Workflow](#git-workflow)

---

## 🎯 Code Quality

### Type Hints (PEP 484)

**✅ DO:**
```python
def predict_consumption(
    temperature: float,
    humidity: float,
    occupancy: int
) -> Dict[str, Any]:
    """Type hints improve IDE support and catch errors early"""
    return {"prediction": 1250.5}
```

**❌ DON'T:**
```python
def predict_consumption(temperature, humidity, occupancy):
    # No type hints = harder to maintain
    return {"prediction": 1250.5}
```

### Docstrings (Google Style)

**✅ DO:**
```python
async def record_energy_reading(
    device_id: str,
    consumption: float,
) -> Dict[str, Any]:
    """
    Record a new energy consumption reading.
    
    Args:
        device_id: Unique device identifier
        consumption: Energy consumption in kWh
    
    Returns:
        Dictionary containing recording status and metadata
    
    Raises:
        ValidationError: If input validation fails
        DatabaseException: If database write fails
    
    Example:
        >>> await record_energy_reading("sensor_001", 1250.5)
        {"success": True, "device_id": "sensor_001"}
    """
    pass
```

### Code Formatting

**Tools:**
- **Black**: Code formatter (PEP 8 compliant)
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Static type checking

**Run all:**
```bash
black backend/ ml/ tests/
isort backend/ ml/ tests/
flake8 backend/ ml/ tests/ --max-line-length=100
mypy backend/ ml/ --strict
```

### Function Design

**Single Responsibility:**
```python
# ✅ Good - Each function does one thing
async def validate_reading(reading: dict) -> None:
    """Validate energy reading"""
    ...

async def save_reading(reading: dict) -> None:
    """Save to database"""
    ...

async def notify_anomaly(reading: dict) -> None:
    """Send notification"""
    ...

# ❌ Bad - Function does too much
async def process_reading(reading: dict):
    # Validate
    # Save
    # Notify
    # Calculate statistics
    # Update cache
    ...
```

---

## 🏗️ Architecture Patterns

### 1. Repository Pattern

**Purpose:** Abstract data access logic

```python
# Define interface
class IEnergyRepository(ABC):
    @abstractmethod
    async def save(self, data: EnergyData) -> None:
        pass
    
    @abstractmethod
    async def find_by_id(self, id: str) -> Optional[EnergyData]:
        pass

# Implement concrete repository
class InfluxDBEnergyRepository(IEnergyRepository):
    async def save(self, data: EnergyData) -> None:
        # InfluxDB-specific implementation
        pass

# Easy to swap implementations
class MockEnergyRepository(IEnergyRepository):
    async def save(self, data: EnergyData) -> None:
        # Mock for testing
        pass
```

### 2. Service Layer Pattern

**Purpose:** Encapsulate business logic

```python
class EnergyService:
    """
    Business logic for energy management
    Coordinates between repositories and models
    """
    
    def __init__(
        self,
        repository: IEnergyRepository,
        ml_model: IPredictionModel,
        notification_service: INotificationService,
    ):
        self.repository = repository
        self.ml_model = ml_model
        self.notification_service = notification_service
    
    async def process_reading(self, reading: EnergyReading) -> ProcessResult:
        """
        Process energy reading with business rules:
        1. Validate input
        2. Detect anomalies
        3. Save to database
        4. Send alerts if needed
        5. Update statistics
        """
        # Validation
        self._validate(reading)
        
        # Anomaly detection
        if self._is_anomaly(reading):
            await self.notification_service.send_alert(reading)
        
        # Save
        await self.repository.save(reading)
        
        return ProcessResult(success=True)
```

### 3. Dependency Injection

**Purpose:** Loose coupling, easier testing

```python
# ✅ Good - Dependencies injected
class EnergyService:
    def __init__(self, repository: IEnergyRepository):
        self.repository = repository  # Injected

# ❌ Bad - Hard-coded dependency
class EnergyService:
    def __init__(self):
        self.repository = InfluxDBRepository()  # Tightly coupled
```

**FastAPI Integration:**
```python
# Define dependency
async def get_energy_service(
    repository: IEnergyRepository = Depends(get_repository),
    ml_model: IModel = Depends(get_ml_model),
) -> EnergyService:
    return EnergyService(repository, ml_model)

# Use in endpoint
@router.post("/readings")
async def create_reading(
    reading: EnergyReading,
    service: EnergyService = Depends(get_energy_service),
):
    return await service.process_reading(reading)
```

---

## 🧪 Testing Strategy

### Testing Pyramid

```
        ┌──────┐
       │  E2E   │    5%  - Full system tests
      ├────────┤
     │Integration│  25% - API + DB tests
    ├──────────┤
   │  Unit Tests │  70% - Fast, isolated
  └────────────┘
```

### Unit Testing

**Test structure (AAA pattern):**
```python
@pytest.mark.unit
async def test_record_energy_reading_success():
    # Arrange (Setup)
    service = EnergyService(mock_repository)
    reading = create_test_reading()
    
    # Act (Execute)
    result = await service.record_reading(reading)
    
    # Assert (Verify)
    assert result.success is True
    mock_repository.save.assert_called_once()
```

**Test naming convention:**
```python
def test_<method_name>_<scenario>_<expected_outcome>():
    # Examples:
    test_record_reading_valid_data_succeeds()
    test_record_reading_invalid_temperature_raises_error()
    test_predict_consumption_no_model_raises_exception()
```

### Fixtures for Reusability

```python
# conftest.py
@pytest.fixture
def sample_energy_reading():
    return EnergyReading(
        device_id="sensor_001",
        temperature=22.5,
        consumption=1250.0,
    )

# Use in tests
def test_validation(sample_energy_reading):
    # Reading already created!
    assert sample_energy_reading.temperature == 22.5
```

### Test Coverage Goals

- **Overall**: > 80%
- **Business logic (services)**: > 90%
- **API endpoints**: > 75%
- **Utilities**: > 85%

**Check coverage:**
```bash
pytest --cov=backend --cov=ml --cov-report=html
```

---

## ⚠️ Error Handling

### Custom Exceptions

```python
# Define domain exceptions
class ValidationError(EnerSightException):
    """Input validation failed"""
    pass

class PredictionError(MLException):
    """ML prediction failed"""
    pass

# Use in code
def validate_temperature(temp: float) -> None:
    if not -50 <= temp <= 60:
        raise ValidationError(
            f"Temperature {temp}°C out of range",
            field="temperature",
            details={"value": temp, "min": -50, "max": 60}
        )
```

### Error Response Format

**Consistent structure:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Temperature out of valid range",
    "type": "ValidationError",
    "details": {
      "field": "temperature",
      "value": 100.0,
      "min": -50,
      "max": 60
    }
  }
}
```

### Error Logging

```python
try:
    result = await service.process_reading(reading)
except ValidationError as e:
    logger.warning(
        f"Validation failed: {e.message}",
        extra={"error_code": e.code, "details": e.details}
    )
    raise
except Exception as e:
    logger.error(
        f"Unexpected error: {e}",
        exc_info=True,  # Include stack trace
        extra={"reading_id": reading.id}
    )
    raise
```

---

## ⚡ Performance Optimization

### 1. Database Query Optimization

**✅ DO - Use batching:**
```python
# Batch insert
await repository.write_batch(readings)  # One query

# ❌ Don't loop
for reading in readings:
    await repository.write(reading)  # N queries
```

**✅ DO - Use indexes:**
```sql
CREATE INDEX idx_readings_timestamp ON energy_readings(timestamp);
CREATE INDEX idx_readings_device_id ON energy_readings(device_id);
```

### 2. Caching Strategy

```python
from functools import lru_cache
import asyncio

# Cache expensive computations
@lru_cache(maxsize=128)
def calculate_statistics(data_hash: str) -> Statistics:
    # Expensive calculation
    return stats

# Async caching with Redis
async def get_cached_prediction(features: Features) -> Prediction:
    cache_key = f"prediction:{hash(features)}"
    
    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return Prediction.parse_raw(cached)
    
    # Compute and cache
    prediction = await ml_model.predict(features)
    await redis.setex(cache_key, ttl=300, value=prediction.json())
    return prediction
```

### 3. Async Operations

**✅ DO - Parallel execution:**
```python
# Execute concurrently
results = await asyncio.gather(
    fetch_energy_data(),
    fetch_weather_data(),
    fetch_occupancy_data(),
)

# ❌ Don't execute sequentially
energy = await fetch_energy_data()
weather = await fetch_weather_data()
occupancy = await fetch_occupancy_data()
```

### 4. ML Model Optimization

```python
# Batch predictions
predictions = model.predict_batch(features_list)  # Vectorized

# ❌ Don't predict one by one
predictions = [model.predict(f) for f in features_list]

# Use model quantization for faster inference
# Lazy load models to save memory
```

---

## 🔒 Security Best Practices

### 1. Input Validation

```python
from pydantic import BaseModel, Field, validator

class EnergyReading(BaseModel):
    temperature: float = Field(..., ge=-50, le=60)
    humidity: float = Field(..., ge=0, le=100)
    consumption: float = Field(..., ge=0)
    
    @validator("temperature")
    def validate_temperature(cls, v):
        if not -50 <= v <= 60:
            raise ValueError("Temperature out of range")
        return v
```

### 2. Authentication & Authorization

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    token: str = Depends(security)
) -> User:
    user = await verify_token(token)
    if not user:
        raise HTTPException(401, "Invalid authentication")
    return user

@router.get("/sensitive-data")
async def get_data(user: User = Depends(get_current_user)):
    # Only authenticated users can access
    pass
```

### 3. Environment Variables

```python
# ✅ DO - Use environment variables
SECRET_KEY = os.getenv("SECRET_KEY")

# ❌ DON'T - Hard-code secrets
SECRET_KEY = "my-secret-key"  # NEVER DO THIS
```

### 4. SQL Injection Prevention

```python
# ✅ DO - Use parameterized queries
await db.execute(
    "SELECT * FROM readings WHERE device_id = :device_id",
    {"device_id": device_id}
)

# ❌ DON'T - String concatenation
await db.execute(
    f"SELECT * FROM readings WHERE device_id = '{device_id}'"
)
```

---

## 📖 Documentation

### Code Documentation

1. **Module docstrings** - Purpose of each file
2. **Class docstrings** - What the class does
3. **Function docstrings** - Args, returns, raises, examples
4. **Type hints** - Parameter and return types
5. **Comments** - Only for complex logic

### API Documentation

**FastAPI auto-generates OpenAPI docs:**

```python
@router.post(
    "/readings",
    summary="Create energy reading",
    description="Record a new energy consumption reading from IoT sensor",
    response_model=ReadingResponse,
    status_code=201,
    tags=["Energy"],
)
async def create_reading(
    reading: EnergyReading = Body(..., example={
        "device_id": "sensor_001",
        "temperature": 22.5,
        "consumption": 1250.0,
    }),
) -> ReadingResponse:
    """
    Create a new energy reading.
    
    - **device_id**: Unique sensor identifier
    - **temperature**: Ambient temperature in Celsius
    - **consumption**: Total energy consumption in kWh
    """
    pass
```

Visit `/api/docs` for interactive documentation!

### Project Documentation

**Required files:**
- `README.md` - Project overview, quick start
- `ARCHITECTURE.md` - Architecture decisions
- `SETUP_GUIDE.md` - Detailed setup instructions
- `API_REFERENCE.md` - API endpoint documentation
- `DEPLOYMENT.md` - Deployment procedures

---

## 🔄 Git Workflow

### Commit Messages (Conventional Commits)

```bash
# Format: <type>(<scope>): <subject>

feat(api): add energy reading endpoint
fix(ml): correct LSTM prediction shape
docs(readme): update installation instructions
test(services): add unit tests for energy service
refactor(repositories): simplify query logic
perf(api): add caching for statistics endpoint
chore(deps): update FastAPI to 0.109.0
```

### Branch Strategy

```
main
├── develop
    ├── feature/energy-endpoints
    ├── feature/ml-predictions
    ├── bugfix/temperature-validation
    └── hotfix/security-patch
```

### Pull Request Checklist

- [ ] All tests pass
- [ ] Code coverage > 80%
- [ ] Type hints added
- [ ] Docstrings written
- [ ] API docs updated
- [ ] No security vulnerabilities
- [ ] Formatted with black
- [ ] Linted with flake8

---

## 🎓 Academic Excellence Criteria

### For End-of-Study Project Evaluation

✅ **Software Architecture** (25%)
- Clean Architecture implementation
- Design patterns applied correctly
- SOLID principles followed
- Well-documented architecture decisions

✅ **Code Quality** (20%)
- Type hints throughout
- Comprehensive docstrings
- PEP 8 compliance
- No code smells

✅ **Testing** (15%)
- Unit test coverage > 80%
- Integration tests for APIs
- Test fixtures and mocks
- Automated test execution

✅ **Documentation** (15%)
- Clear README with setup instructions
- Architecture documentation
- API documentation (OpenAPI)
- Code comments where needed

✅ **Best Practices** (15%)
- Error handling strategy
- Logging with context
- Configuration management
- Security considerations

✅ **Innovation** (10%)
- ML integration
- Real-time data processing
- Scalable architecture
- Modern tech stack

---

## 📝 Quick Reference Commands

### Development

```bash
# Run backend server
python -m uvicorn backend.main:app --reload

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=backend --cov-report=html

# Format code
black backend/ ml/ tests/

# Lint code
flake8 backend/ ml/ --max-line-length=100

# Type check
mypy backend/ --strict
```

### Docker (Future)

```bash
# Build image
docker build -t enersight:latest .

# Run container
docker run -p 8000:8000 enersight:latest

# Docker Compose
docker-compose up -d
```

---

**Remember:** Write code as if the person maintaining it is a violent psychopath who knows where you live. Make it clean, documented, and testable! 🎯
