# Alert System API Test Script
# Tests all alert endpoints

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  EnerSight Alert System API Tests" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$baseUrl = "http://localhost:8000"
$testResults = @()

# Function to print test result
function Test-Endpoint {
    param (
        [string]$TestName,
        [bool]$Success,
        [string]$Message = ""
    )
    
    if ($Success) {
        Write-Host "[PASS] " -ForegroundColor Green -NoNewline
        Write-Host $TestName
        $script:passCount++
    } else {
        Write-Host "[FAIL] " -ForegroundColor Red -NoNewline
        Write-Host "$TestName - $Message"
        $script:failCount++
    }
}

$script:passCount = 0
$script:failCount = 0

# Step 1: Login to get token
Write-Host "`n1. Logging in..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = "johndoe"
        password = "SecurePass123!"
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/login" -Method Post -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    
    Test-Endpoint "Login successful" $true
    Write-Host "   Token: $($token.Substring(0, 30))..." -ForegroundColor Gray
} catch {
    Test-Endpoint "Login" $false $_.Exception.Message
    Write-Host "`nCannot proceed without authentication. Exiting." -ForegroundColor Red
    exit 1
}

# Set headers with authorization
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

# Step 2: Check initial alert summary
Write-Host "`n2. Getting alert summary..." -ForegroundColor Yellow
try {
    $summaryResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/summary" -Method Get -Headers $headers
    
    Test-Endpoint "Get alert summary" $true
    Write-Host "   Total alerts: $($summaryResponse.total_alerts)" -ForegroundColor Gray
    Write-Host "   Pending: $($summaryResponse.pending_alerts)" -ForegroundColor Gray
    Write-Host "   Critical: $($summaryResponse.critical_alerts)" -ForegroundColor Gray
    Write-Host "   Unacknowledged: $($summaryResponse.unacknowledged_alerts)" -ForegroundColor Gray
    Write-Host "   Today: $($summaryResponse.alerts_today)" -ForegroundColor Gray
} catch {
    Test-Endpoint "Get alert summary" $false $_.Exception.Message
}

# Step 3: Create a test alert
Write-Host "`n3. Creating test alert..." -ForegroundColor Yellow
try {
    $alertBody = @{
        user_id = $loginResponse.user_id
        alert_type = "threshold_exceeded"
        severity = "warning"
        title = "Test Alert - Energy Threshold"
        message = "This is a test alert. Your energy consumption exceeded 1000 kWh."
        current_value = 1250.5
        threshold_value = 1000.0
    } | ConvertTo-Json

    $createResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/" -Method Post -Body $alertBody -Headers $headers
    $alertId = $createResponse.id
    
    Test-Endpoint "Create alert" $true
    Write-Host "   Alert ID: $alertId" -ForegroundColor Gray
    Write-Host "   Status: $($createResponse.status)" -ForegroundColor Gray
} catch {
    Test-Endpoint "Create alert" $false $_.Exception.Message
    $alertId = $null
}

# Step 4: Get all alerts
Write-Host "`n4. Getting all alerts..." -ForegroundColor Yellow
try {
    $alertsResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/" -Method Get -Headers $headers
    
    Test-Endpoint "Get all alerts" $true
    Write-Host "   Found $($alertsResponse.Count) alerts" -ForegroundColor Gray
    if ($alertsResponse.Count -gt 0) {
        Write-Host "   Latest: $($alertsResponse[0].title)" -ForegroundColor Gray
    }
} catch {
    Test-Endpoint "Get all alerts" $false $_.Exception.Message
}

# Step 5: Get specific alert
if ($alertId) {
    Write-Host "`n5. Getting specific alert..." -ForegroundColor Yellow
    try {
        $alertResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/$alertId" -Method Get -Headers $headers
        
        Test-Endpoint "Get alert by ID" $true
        Write-Host "   Title: $($alertResponse.title)" -ForegroundColor Gray
        Write-Host "   Type: $($alertResponse.alert_type)" -ForegroundColor Gray
        Write-Host "   Severity: $($alertResponse.severity)" -ForegroundColor Gray
    } catch {
        Test-Endpoint "Get alert by ID" $false $_.Exception.Message
    }
}

# Step 6: Filter alerts by status
Write-Host "`n6. Filtering alerts by status (pending)..." -ForegroundColor Yellow
try {
    $filteredResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/?status=pending" -Method Get -Headers $headers
    
    Test-Endpoint "Filter alerts by status" $true
    Write-Host "   Pending alerts: $($filteredResponse.Count)" -ForegroundColor Gray
} catch {
    Test-Endpoint "Filter alerts by status" $false $_.Exception.Message
}

# Step 7: Acknowledge alert
if ($alertId) {
    Write-Host "`n7. Acknowledging alert..." -ForegroundColor Yellow
    try {
        $ackResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/$alertId/acknowledge" -Method Post -Headers $headers
        
        Test-Endpoint "Acknowledge alert" $true
        Write-Host "   Status: $($ackResponse.status)" -ForegroundColor Gray
        Write-Host "   Acknowledged at: $($ackResponse.acknowledged_at)" -ForegroundColor Gray
    } catch {
        Test-Endpoint "Acknowledge alert" $false $_.Exception.Message
    }
}

# Step 8: Resolve alert
if ($alertId) {
    Write-Host "`n8. Resolving alert..." -ForegroundColor Yellow
    try {
        $resolveResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/$alertId/resolve" -Method Post -Headers $headers
        
        Test-Endpoint "Resolve alert" $true
        Write-Host "   Status: $($resolveResponse.status)" -ForegroundColor Gray
        Write-Host "   Resolved at: $($resolveResponse.resolved_at)" -ForegroundColor Gray
    } catch {
        Test-Endpoint "Resolve alert" $false $_.Exception.Message
    }
}

# Step 9: Update alert using PATCH
if ($alertId) {
    Write-Host "`n9. Updating alert using PATCH..." -ForegroundColor Yellow
    try {
        $updateBody = @{
            status = "resolved"
        } | ConvertTo-Json

        $updateResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/$alertId" -Method Patch -Body $updateBody -Headers $headers
        
        Test-Endpoint "Update alert (PATCH)" $true
        Write-Host "   Updated status: $($updateResponse.status)" -ForegroundColor Gray
    } catch {
        Test-Endpoint "Update alert (PATCH)" $false $_.Exception.Message
    }
}

# Step 10: Check updated summary
Write-Host "`n10. Getting updated alert summary..." -ForegroundColor Yellow
try {
    $finalSummary = Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/summary" -Method Get -Headers $headers
    
    Test-Endpoint "Get updated summary" $true
    Write-Host "   Total alerts: $($finalSummary.total_alerts)" -ForegroundColor Gray
    Write-Host "   Pending: $($finalSummary.pending_alerts)" -ForegroundColor Gray
    Write-Host "   Unacknowledged: $($finalSummary.unacknowledged_alerts)" -ForegroundColor Gray
} catch {
    Test-Endpoint "Get updated summary" $false $_.Exception.Message
}

# Step 11: Delete test alert (cleanup)
if ($alertId) {
    Write-Host "`n11. Deleting test alert (cleanup)..." -ForegroundColor Yellow
    try {
        Invoke-RestMethod -Uri "$baseUrl/api/v1/alerts/$alertId" -Method Delete -Headers $headers
        
        Test-Endpoint "Delete alert" $true
    } catch {
        Test-Endpoint "Delete alert" $false $_.Exception.Message
    }
}

# Summary
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Test Results" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Passed: " -NoNewline
Write-Host $script:passCount -ForegroundColor Green
Write-Host "Failed: " -NoNewline
Write-Host $script:failCount -ForegroundColor Red
Write-Host "Total:  $($script:passCount + $script:failCount)" -ForegroundColor Cyan

if ($script:failCount -eq 0) {
    Write-Host "`n✅ All alert tests passed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️  Some tests failed. Check the output above." -ForegroundColor Yellow
}

Write-Host "`nNote: Alert monitoring service runs every 5 minutes to check thresholds." -ForegroundColor Cyan
Write-Host "To test threshold alerts:" -ForegroundColor Cyan
Write-Host "  1. Lower your alert_threshold_kwh in user preferences" -ForegroundColor Gray
Write-Host "  2. Wait for the monitoring service to run" -ForegroundColor Gray
Write-Host "  3. Check for new alerts" -ForegroundColor Gray
Write-Host ""
