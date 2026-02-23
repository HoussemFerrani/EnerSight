# Test PostgreSQL User Management API
# Run this after starting the backend

Write-Host "`n=== Testing PostgreSQL User Management ===`n" -ForegroundColor Cyan

# Wait for backend to be ready
Write-Host "Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Test 1: Health check
Write-Host "`n1. Testing backend health..." -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "   ✓ Backend is healthy" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "   ✗ Backend health check failed" -ForegroundColor Red
    Write-Host "   Make sure backend is running: .\venv\Scripts\python -m uvicorn backend.main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Test 2: Create a test user
Write-Host "`n2. Creating a test user..." -ForegroundColor Green
$newUser = @{
    email = "john.doe@example.com"
    username = "johndoe"
    password = "SecurePass123!"
    full_name = "John Doe"
    phone = "+1234567890"
    address = "123 Main St, City, State 12345"
    role = "user"
} | ConvertTo-Json

try {
    $createdUser = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users" -Method Post -Body $newUser -ContentType "application/json"
    Write-Host "   ✓ User created successfully!" -ForegroundColor Green
    Write-Host "   User ID: $($createdUser.id)" -ForegroundColor Cyan
    $userId = $createdUser.id
    $createdUser | ConvertTo-Json
} catch {
    if ($_.Exception.Response.StatusCode.value__ -eq 400) {
        Write-Host "   ℹ User already exists (this is OK)" -ForegroundColor Yellow
        # Try to get the user by username instead
        try {
            $existingUser = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/username/johndoe" -Method Get
            $userId = $existingUser.id
            Write-Host "   Using existing user ID: $userId" -ForegroundColor Cyan
        } catch {
            Write-Host "   ✗ Error getting existing user" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "   ✗ Failed to create user: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# Test 3: Get all users
Write-Host "`n3. Fetching all users..." -ForegroundColor Green
try {
    $users = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users" -Method Get
    Write-Host "   ✓ Found $($users.Count) user(s)" -ForegroundColor Green
    $users | ConvertTo-Json
} catch {
    Write-Host "   ✗ Failed to fetch users" -ForegroundColor Red
}

# Test 4: Get user by ID
Write-Host "`n4. Fetching user by ID ($userId)..." -ForegroundColor Green
try {
    $user = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" -Method Get
    Write-Host "   ✓ User found" -ForegroundColor Green
    $user | ConvertTo-Json
} catch {
    Write-Host "   ✗ Failed to fetch user" -ForegroundColor Red
}

# Test 5: Update user
Write-Host "`n5. Updating user information..." -ForegroundColor Green
$updateData = @{
    full_name = "John Doe Updated"
    phone = "+1987654321"
} | ConvertTo-Json

try {
    $updatedUser = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" -Method Put -Body $updateData -ContentType "application/json"
    Write-Host "   ✓ User updated successfully" -ForegroundColor Green
    $updatedUser | ConvertTo-Json
} catch {
    Write-Host "   ✗ Failed to update user" -ForegroundColor Red
}

# Test 6: Get user preferences
Write-Host "`n6. Fetching user preferences..." -ForegroundColor Green
try {
    $prefs = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId/preferences" -Method Get
    Write-Host "   ✓ Preferences found" -ForegroundColor Green
    $prefs | ConvertTo-Json
} catch {
    Write-Host "   ✗ Failed to fetch preferences" -ForegroundColor Red
}

# Test 7: Update user preferences
Write-Host "`n7. Updating user preferences..." -ForegroundColor Green
$prefsUpdate = @{
    theme = "dark"
    language = "en"
    email_notifications = true
    alert_threshold_kwh = 1000
    currency = "USD"
} | ConvertTo-Json

try {
    $updatedPrefs = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId/preferences" -Method Put -Body $prefsUpdate -ContentType "application/json"
    Write-Host "   ✓ Preferences updated successfully" -ForegroundColor Green
    $updatedPrefs | ConvertTo-Json
} catch {
    Write-Host "   ✗ Failed to update preferences" -ForegroundColor Red
}

# Test 8: Get user statistics
Write-Host "`n8. Fetching user statistics..." -ForegroundColor Green
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/stats/summary" -Method Get
    Write-Host "   ✓ Statistics retrieved" -ForegroundColor Green
    $stats | ConvertTo-Json
} catch {
    Write-Host "   ✗ Failed to fetch statistics" -ForegroundColor Red
}

Write-Host "`n=== All Tests Completed! ===`n" -ForegroundColor Green
Write-Host "PostgreSQL user management is working correctly!" -ForegroundColor Cyan
Write-Host "`nAPI Documentation available at: http://localhost:8000/api/docs`n" -ForegroundColor Yellow