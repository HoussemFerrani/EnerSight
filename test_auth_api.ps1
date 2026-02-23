# Authentication API Test Script
# Tests login, token verification, and protected endpoints

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  EnerSight Authentication API Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000/api/v1"
$testsPassed = 0
$testsFailed = 0

# Test 1: Health Check
Write-Host "[Test 1] Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    if ($response.status -eq "healthy") {
        Write-Host "[PASS] Health check passed" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "[FAIL] Health check returned non-healthy status" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "[FAIL] Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 2: Login with existing user
Write-Host "`n[Test 2] Login with existing user (johndoe)..." -ForegroundColor Yellow
try {
    $loginData = @{
        username = "johndoe"
        password = "SecurePass123!"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $loginData -ContentType "application/json"
    
    $global:token = $response.access_token
    
    Write-Host "[PASS] Login successful" -ForegroundColor Green
    Write-Host "  User ID: $($response.user_id)" -ForegroundColor Cyan
    Write-Host "  Username: $($response.username)" -ForegroundColor Cyan
    Write-Host "  Email: $($response.email)" -ForegroundColor Cyan
    Write-Host "  Token expires in: $($response.expires_in) seconds" -ForegroundColor Cyan
    $testsPassed++
} catch {
    Write-Host "[FAIL] Login failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
    if ($_.ErrorDetails.Message) {
        $errorResponse = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "  Detail: $($errorResponse.detail)" -ForegroundColor Red
    }
}

# Test 3: Verify Token
Write-Host "`n[Test 3] Verify authentication token..." -ForegroundColor Yellow
try {
    $headers = @{ Authorization = "Bearer $global:token" }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/verify" -Method Get -Headers $headers
    
    if ($response.valid -eq $true) {
        Write-Host "[PASS] Token verification successful" -ForegroundColor Green
        Write-Host "  User: $($response.username) (Role: $($response.role))" -ForegroundColor Cyan
        $testsPassed++
    } else {
        Write-Host "[FAIL] Token marked as invalid" -ForegroundColor Red
        $testsFailed++
    }
} catch {
    Write-Host "[FAIL] Token verification failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 4: Get Current User Profile
Write-Host "`n[Test 4] Get current user profile..." -ForegroundColor Yellow
try {
    $headers = @{ Authorization = "Bearer $global:token" }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/me" -Method Get -Headers $headers
    
    Write-Host "[PASS] Retrieved user profile" -ForegroundColor Green
    Write-Host "  ID: $($response.id)" -ForegroundColor Cyan
    Write-Host "  Username: $($response.username)" -ForegroundColor Cyan
    Write-Host "  Email: $($response.email)" -ForegroundColor Cyan
    Write-Host "  Role: $($response.role)" -ForegroundColor Cyan
    Write-Host "  Active: $($response.is_active)" -ForegroundColor Cyan
    $testsPassed++
} catch {
    Write-Host "[FAIL] Failed to get profile: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 5: Access Protected User Endpoint
Write-Host "`n[Test 5] Access protected user endpoint..." -ForegroundColor Yellow
try {
    $headers = @{ Authorization = "Bearer $global:token" }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/users/1" -Method Get -Headers $headers
    
    Write-Host "[PASS] Accessed protected endpoint" -ForegroundColor Green
    Write-Host "  Retrieved user: $($response.username)" -ForegroundColor Cyan
    $testsPassed++
} catch {
    Write-Host "[FAIL] Failed to access protected endpoint: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 6: Refresh Token
Write-Host "`n[Test 6] Refresh authentication token..." -ForegroundColor Yellow
try {
    $headers = @{ Authorization = "Bearer $global:token" }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/refresh" -Method Post -Headers $headers
    
    $newToken = $response.access_token
    
    Write-Host "[PASS] Token refresh successful" -ForegroundColor Green
    Write-Host "  New token expires in: $($response.expires_in) seconds" -ForegroundColor Cyan
    $testsPassed++
    
    $global:token = $newToken
} catch {
    Write-Host "[FAIL] Token refresh failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Test 7: Login with invalid credentials (should fail)
Write-Host "`n[Test 7] Try login with invalid credentials (should fail)..." -ForegroundColor Yellow
try {
    $invalidLogin = @{
        username = "johndoe"
        password = "WrongPassword123!"
    } | ConvertTo-Json

    $response = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $invalidLogin -ContentType "application/json" -ErrorAction Stop
    
    Write-Host "[FAIL] Login succeeded with wrong password (security issue!)" -ForegroundColor Red
    $testsFailed++
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        Write-Host "[PASS] Correctly rejected invalid credentials (401)" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host "[FAIL] Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
        $testsFailed++
    }
}

# Test 8: Logout
Write-Host "`n[Test 8] Logout user..." -ForegroundColor Yellow
try {
    $headers = @{ Authorization = "Bearer $global:token" }
    
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/logout" -Method Post -Headers $headers
    
    Write-Host "[PASS] Logout successful" -ForegroundColor Green
    Write-Host "  Message: $($response.message)" -ForegroundColor Cyan
    $testsPassed++
} catch {
    Write-Host "[FAIL] Logout failed: $($_.Exception.Message)" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "           Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "Tests Failed: $testsFailed" -ForegroundColor Red
Write-Host "Total Tests:  $($testsPassed + $testsFailed)" -ForegroundColor Cyan

if ($testsFailed -eq 0) {
    Write-Host "`nAll Tests Passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`nSome Tests Failed" -ForegroundColor Red
    exit 1
}
