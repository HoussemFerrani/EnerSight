# Test script for Enhanced Analytics API
# Comprehensive testing of all analytics endpoints

$baseUrl = "http://localhost:8000"
$apiBase = "$baseUrl/api/v1"

# Color output functions
function Write-Success {
    param([string]$message)
    Write-Host "✓ $message" -ForegroundColor Green
}

function Write-Failure {
    param([string]$message)
    Write-Host "✗ $message" -ForegroundColor Red
}

function Write-Info {
    param([string]$message)
    Write-Host "ℹ $message" -ForegroundColor Cyan
}

function Write-TestHeader {
    param([string]$message)
    Write-Host "`n=== $message ===" -ForegroundColor Yellow
}

# Counter for tests
$testsRun = 0
$testsPassed = 0
$testsFailed = 0

# Test function
function Test-Endpoint {
    param(
        [string]$name,
        [string]$method,
        [string]$endpoint,
        [hashtable]$headers = @{},
        [object]$body = $null,
        [scriptblock]$validator
    )
    
    $script:testsRun++
    Write-Info "Testing: $name"
    
    try {
        $params = @{
            Uri = "$apiBase$endpoint"
            Method = $method
            Headers = $headers
            ContentType = "application/json"
        }
        
        if ($body) {
            $params.Body = ($body | ConvertTo-Json -Depth 10)
        }
        
        $response = Invoke-RestMethod @params
        
        # Run custom validator if provided
        if ($validator) {
            $validationResult = & $validator $response
            if ($validationResult -eq $false) {
                throw "Validation failed"
            }
        }
        
        Write-Success "$name - PASSED"
        $script:testsPassed++
        return $response
    }
    catch {
        Write-Failure "$name - FAILED: $($_.Exception.Message)"
        $script:testsFailed++
        return $null
    }
}

# Start tests
Write-TestHeader "Enhanced Analytics API Tests"
Write-Host "Base URL: $baseUrl`n"

# Step 1: Login to get token
Write-TestHeader "1. Authentication"
$loginResponse = Test-Endpoint `
    -name "Login" `
    -method "POST" `
    -endpoint "/auth/login" `
    -body @{
        username = "johndoe"
        password = "SecurePass123!"
    } `
    -validator {
        param($resp)
        return ($resp.access_token -and $resp.token_type -eq "bearer")
    }

if (-not $loginResponse) {
    Write-Failure "Login failed. Cannot continue with tests."
    exit 1
}

$token = $loginResponse.access_token
$authHeaders = @{
    "Authorization" = "Bearer $token"
}

Write-Success "Authentication successful"
Write-Info "Token: $($token.Substring(0, 20))..."

# Step 2: Test Summary Endpoint
Write-TestHeader "2. Get Summary"
$startDate = (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ss")
$endDate = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")

$summaryResponse = Test-Endpoint `
    -name "Get Summary" `
    -method "GET" `
    -endpoint "/analytics/summary?start_date=$startDate&end_date=$endDate&cost_per_kwh=0.12" `
    -headers $authHeaders `
    -validator {
        param($resp)
        return ($resp.total_consumption -ne $null -and $resp.average_daily -ne $null)
    }

if ($summaryResponse) {
    Write-Host "  Total Consumption: $($summaryResponse.total_consumption) kWh" -ForegroundColor White
    Write-Host "  Average Daily: $($summaryResponse.average_daily) kWh/day" -ForegroundColor White
    if ($summaryResponse.total_cost) {
        Write-Host "  Total Cost: $$($summaryResponse.total_cost)" -ForegroundColor White
    }
}

# Step 3: Test Date Range Endpoint
Write-TestHeader "3. Get Data by Date Range"
$dateRangeBody = @{
    start_date = $startDate
    end_date = $endDate
    aggregation = "day"
}

$dateRangeResponse = Test-Endpoint `
    -name "Get Date Range Data" `
    -method "POST" `
    -endpoint "/analytics/date-range" `
    -headers $authHeaders `
    -body $dateRangeBody `
    -validator {
        param($resp)
        return ($resp -is [array])
    }

if ($dateRangeResponse) {
    Write-Host "  Data points retrieved: $($dateRangeResponse.Count)" -ForegroundColor White
}

# Step 4: Test Aggregated Data
Write-TestHeader "4. Get Aggregated Data"
$aggregationResponse = Test-Endpoint `
    -name "Get Aggregated Data (Daily)" `
    -method "GET" `
    -endpoint "/analytics/aggregated?start_date=$startDate&end_date=$endDate&period=day" `
    -headers $authHeaders `
    -validator {
        param($resp)
        return ($resp -is [array])
    }

if ($aggregationResponse -and $aggregationResponse.Count -gt 0) {
    Write-Host "  Aggregated periods: $($aggregationResponse.Count)" -ForegroundColor White
    $firstPeriod = $aggregationResponse[0]
    if ($firstPeriod.total) {
        Write-Host "  First period total: $($firstPeriod.total) kWh" -ForegroundColor White
    }
}

# Step 5: Test Cost Calculation
Write-TestHeader "5. Calculate Cost"
$costResponse = Test-Endpoint `
    -name "Calculate Energy Cost" `
    -method "GET" `
    -endpoint "/analytics/cost?start_date=$startDate&end_date=$endDate&cost_per_kwh=0.15" `
    -headers $authHeaders `
    -validator {
        param($resp)
        return ($resp.total_kwh -ne $null -and $resp.total_cost -ne $null)
    }

if ($costResponse) {
    Write-Host "  Total kWh: $($costResponse.total_kwh)" -ForegroundColor White
    Write-Host "  Cost per kWh: $$($costResponse.cost_per_kwh)" -ForegroundColor White
    Write-Host "  Total Cost: $$($costResponse.total_cost)" -ForegroundColor White
}

# Step 6: Test Period Comparison
Write-TestHeader "6. Compare Periods"
$comparisonTypes = @("previous_period", "same_period_last_month", "same_period_last_year")

foreach ($compType in $comparisonTypes) {
    $comparisonResponse = Test-Endpoint `
        -name "Compare: $compType" `
        -method "GET" `
        -endpoint "/analytics/compare?current_start=$startDate&current_end=$endDate&comparison_type=$compType" `
        -headers $authHeaders `
        -validator {
            param($resp)
            return ($resp.current_period -and $resp.comparison_period -and $resp.difference -ne $null)
        }
    
    if ($comparisonResponse) {
        Write-Host "  Current: $($comparisonResponse.current_period.total) kWh" -ForegroundColor White
        Write-Host "  Comparison: $($comparisonResponse.comparison_period.total) kWh" -ForegroundColor White
        Write-Host "  Difference: $($comparisonResponse.difference) kWh ($($comparisonResponse.percentage_change)%)" -ForegroundColor White
    }
}

# Step 7: Test Quick Stats
Write-TestHeader "7. Get Quick Stats"
$quickStatsResponse = Test-Endpoint `
    -name "Get Quick Stats" `
    -method "GET" `
    -endpoint "/analytics/quick-stats" `
    -headers $authHeaders `
    -validator {
        param($resp)
        return ($resp.today -and $resp.this_week -and $resp.this_month)
    }

if ($quickStatsResponse) {
    Write-Host "  Today: $($quickStatsResponse.today.total) kWh" -ForegroundColor White
    Write-Host "  This Week: $($quickStatsResponse.this_week.total) kWh" -ForegroundColor White
    Write-Host "  This Month: $($quickStatsResponse.this_month.total) kWh" -ForegroundColor White
    Write-Host "  Last 24h: $($quickStatsResponse.last_24h.total) kWh" -ForegroundColor White
}

# Step 8: Test Trends
Write-TestHeader "8. Get Trends"
$trendsResponse = Test-Endpoint `
    -name "Get 30-Day Trends" `
    -method "GET" `
    -endpoint "/analytics/trends?days=30" `
    -headers $authHeaders `
    -validator {
        param($resp)
        return ($resp.trend_direction -and $resp.daily_data -is [array])
    }

if ($trendsResponse) {
    Write-Host "  Trend Direction: $($trendsResponse.trend_direction)" -ForegroundColor White
    Write-Host "  Trend Percentage: $($trendsResponse.trend_percentage)%" -ForegroundColor White
    Write-Host "  Daily Data Points: $($trendsResponse.daily_data.Count)" -ForegroundColor White
}

# Step 9: Test CSV Export
Write-TestHeader "9. Export to CSV"
Write-Info "Testing CSV Export (without downloading)"
try {
    $exportUrl = "$apiBase/analytics/export/csv?start_date=$startDate&end_date=$endDate&aggregation=day"
    $exportHeaders = @{
        "Authorization" = "Bearer $token"
    }
    
    $response = Invoke-WebRequest -Uri $exportUrl -Headers $exportHeaders -Method GET
    
    if ($response.StatusCode -eq 200 -and $response.Headers["Content-Type"] -like "*csv*") {
        Write-Success "CSV Export - PASSED"
        $script:testsPassed++
        Write-Host "  Content-Type: $($response.Headers["Content-Type"])" -ForegroundColor White
        $contentLength = $response.Content.Length
        Write-Host "  Content Size: $contentLength bytes" -ForegroundColor White
    }
    else {
        Write-Failure "CSV Export - FAILED: Unexpected response"
        $script:testsFailed++
    }
    $script:testsRun++
}
catch {
    Write-Failure "CSV Export - FAILED: $($_.Exception.Message)"
    $script:testsFailed++
    $script:testsRun++
}

# Summary
Write-TestHeader "Test Summary"
Write-Host "Total Tests: $testsRun" -ForegroundColor White
Write-Host "Passed: $testsPassed" -ForegroundColor Green
Write-Host "Failed: $testsFailed" -ForegroundColor Red

if ($testsFailed -eq 0) {
    Write-Host "`n🎉 All tests passed!" -ForegroundColor Green
    exit 0
}
else {
    Write-Host "`n⚠️ Some tests failed" -ForegroundColor Yellow
    exit 1
}
