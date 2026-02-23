"""
PostgreSQL Quick Start Guide
============================

PostgreSQL for User Management is now configured!

## Docker Command (Already Done ✓)
```bash
docker compose up -d postgres
```

## Database Details:
- Host: localhost
- Port: 5432
- Database: enersight
- Username: enersight_user
- Password: enersight_pass_123

## Features Added:
✓ User model with authentication fields
✓ User preferences/settings model
✓ Password hashing with bcrypt
✓ JWT token support (for future auth)
✓ User CRUD endpoints

## API Endpoints (once backend starts):

### List all users
GET http://localhost:8000/api/v1/users

### Create a user
POST http://localhost:8000/api/v1/users
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "securePassword123",
  "full_name": "John Doe",
  "role": "user"
}

### Get user by ID
GET http://localhost:8000/api/v1/users/{user_id}

### Update user
PUT http://localhost:8000/api/v1/users/{user_id}
{
  "full_name": "Jane Doe Updated",
  "phone": "+1234567890"
}

### Delete user
DELETE http://localhost:8000/api/v1/users/{user_id}

### Change password
POST http://localhost:8000/api/v1/users/{user_id}/change-password
{
  "old_password": "oldPassword",
  "new_password": "newPassword123"
}

### Get user preferences
GET http://localhost:8000/api/v1/users/{user_id}/preferences

### Update preferences
PUT http://localhost:8000/api/v1/users/{user_id}/preferences
{
  "theme": "dark",
  "email_notifications": false,
  "alert_threshold_kwh": 1000
}

### Get user statistics
GET http://localhost:8000/api/v1/users/stats/summary

## To Connect from Python:
```python
from backend.database.postgres import get_db, init_db

# Initialize database (creates tables)
init_db()

# Use in API endpoint
from fastapi import Depends
from sqlalchemy.orm import Session

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users
```

## Database Tables Created:
1. `users` - User authentication and profile
   - id, email, username, hashed_password
   - full_name, phone, address
   - role (admin/user/viewer)
   - is_active, is_verified
   - created_at, updated_at, last_login

2. `user_preferences` - User settings
   - id, user_id
   - theme, language, timezone
   - email_notifications, push_notifications
   - alert_threshold_kwh
   - date_format, currency, energy_unit
   - created_at, updated_at

## Next Steps:
1. Start the backend: `.\venv\Scripts\python -m uvicorn backend.main:app --reload`
2. Visit API docs: http://localhost:8000/api/docs
3. Test the user endpoints!
4. For full authentication (login/logout), proceed to Option 8

## Stopping PostgreSQL:
```bash
docker compose stop postgres
```

## Viewing PostgreSQL logs:
```bash
docker compose logs postgres
```

## Accessing PostgreSQL CLI:
```bash
docker exec -it enersight-postgres psql -U enersight_user -d enersight
```

Common SQL commands:
- `\dt` - List tables
- `\d users` - Describe users table
- `SELECT * FROM users;` - View all users
- `\q` - Quit
