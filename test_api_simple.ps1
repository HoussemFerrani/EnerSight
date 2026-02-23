# Simple PostgreSQL API Test
Write-Host "Testing PostgreSQL User Management API" -ForegroundColor Cyan

# Test 1: Health check
Write-Host "`nTest 1: Health Check" -ForegroundColor Green
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "SUCCESS - Backend is healthy" -ForegroundColor Green
    $health | ConvertTo-Json
} catch {
    Write-Host "FAILED - Backend not responding" -ForegroundColor Red
    exit 1
}

# Test 2: Create user
Write-Host "`nTest 2: Create User" -ForegroundColor Green
$newUser = @{
    email = "john.doe@example.com"
    username = "johndoe"
    password = "SecurePass123!"
    full_name = "John Doe"
    role = "user"
} | ConvertTo-Json

try {
    $user = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users" -Method Post -Body $newUser -ContentType "application/json" -ErrorAction Stop
    Write-Host "SUCCESS - User created (ID: $($user.id))" -ForegroundColor Green
    $userId = $user.id
} catch {
    if ($_ -match "400") {
        Write-Host "INFO - User already exists, fetching..." -ForegroundColor Yellow
        $user = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/username/johndoe" -Method Get
        $userId = $user.id
        Write-Host "Using existing user ID: $userId" -ForegroundColor Cyan
    } else {
        Write-Host "FAILED - Could not create user: $_" -ForegroundColor Red
        exit 1
    }
}

# Test 3: List users
Write-Host "`nTest 3: List All Users" -ForegroundColor Green
try {
    $users = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users" -Method Get
    Write-Host "SUCCESS - Found $($users.Count) user(s)" -ForegroundColor Green
    $users | ConvertTo-Json -Depth 3
} catch {
    Write-Host "FAILED - Could not list users" -ForegroundColor Red
}

# Test 4: Get user by ID
Write-Host "`nTest 4: Get User by ID" -ForegroundColor Green
try {
    $user = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" -Method Get
    Write-Host "SUCCESS - User found: $($user.username)" -ForegroundColor Green
    $user | ConvertTo-Json -Depth 3
} catch {
    Write-Host "FAILED - Could not get user" -ForegroundColor Red
}

# Test 5: Update user
Write-Host "`nTest 5: Update User" -ForegroundColor Green
$update = @{
    full_name = "John Doe Updated"
    phone = "+1234567890"
} | ConvertTo-Json

try {
    $updated = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId" -Method Put -Body $update -ContentType "application/json"
    Write-Host "SUCCESS - User updated" -ForegroundColor Green
    Write-Host "New name: $($updated.full_name)" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED - Could not update user" -ForegroundColor Red
}

# Test 6: Get preferences
Write-Host "`nTest 6: Get User Preferences" -ForegroundColor Green
try {
    $prefs = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId/preferences" -Method Get
    Write-Host "SUCCESS - Preferences retrieved" -ForegroundColor Green
    $prefs | ConvertTo-Json -Depth 3
} catch {
    Write-Host "FAILED - Could not get preferences" -ForegroundColor Red
}

# Test 7: Update preferences
Write-Host "`nTest 7: Update Preferences" -ForegroundColor Green
$prefsUpdate = @{
    theme = "dark"
    language = "en"
    email_notifications = $true
    alert_threshold_kwh = 1000
} | ConvertTo-Json

try {
    $updatedPrefs = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/$userId/preferences" -Method Put -Body $prefsUpdate -ContentType "application/json"
    Write-Host "SUCCESS - Preferences updated" -ForegroundColor Green
    Write-Host "Theme: $($updatedPrefs.theme)" -ForegroundColor Cyan
} catch {
    Write-Host "FAILED - Could not update preferences" -ForegroundColor Red
}

# Test 8: Get statistics
Write-Host "`nTest 8: Get User Statistics" -ForegroundColor Green
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/users/stats/summary" -Method Get
    Write-Host "SUCCESS - Statistics retrieved" -ForegroundColor Green
    $stats | ConvertTo-Json -Depth 3
} catch {
    Write-Host "FAILED - Could not get statistics" -ForegroundColor Red
}

Write-Host "`n=== All Tests Completed ===" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/api/docs" -ForegroundColor Yellow
