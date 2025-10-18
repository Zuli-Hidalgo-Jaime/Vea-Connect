# Network diagnostic script for Azure deployment issues
param(
    [string]$ResourceGroupName = "rg-vea-connect-dev",
    [string]$AppServiceName = "veaconnect-webapp-prod"
)

Write-Host "=== NETWORK DIAGNOSTIC FOR AZURE DEPLOYMENT ===" -ForegroundColor Green

# 1. Test basic internet connectivity
Write-Host "1. Testing basic internet connectivity..." -ForegroundColor Yellow
try {
    $pingResult = Test-Connection -ComputerName "8.8.8.8" -Count 2 -Quiet
    if ($pingResult) {
        Write-Host "   OK - Basic internet connectivity working" -ForegroundColor Green
    } else {
        Write-Host "   ERROR - No internet connectivity" -ForegroundColor Red
    }
} catch {
    Write-Host "   ERROR - Internet connectivity test failed: $_" -ForegroundColor Red
}

# 2. Test DNS resolution
Write-Host "2. Testing DNS resolution..." -ForegroundColor Yellow
try {
    $dnsResult = Resolve-DnsName -Name "www.google.com" -ErrorAction SilentlyContinue
    if ($dnsResult) {
        Write-Host "   OK - DNS resolution working" -ForegroundColor Green
    } else {
        Write-Host "   ERROR - DNS resolution failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ERROR - DNS resolution test failed: $_" -ForegroundColor Red
}

# 3. Test Azure endpoints
Write-Host "3. Testing Azure endpoints..." -ForegroundColor Yellow
$azureEndpoints = @(
    "https://management.azure.com",
    "https://login.microsoftonline.com",
    "https://portal.azure.com"
)

foreach ($endpoint in $azureEndpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint -Method Head -TimeoutSec 10 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 401) {
            Write-Host "   OK - $endpoint accessible" -ForegroundColor Green
        } else {
            Write-Host "   WARNING - $endpoint returned status: $($response.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "   ERROR - $endpoint not accessible: $_" -ForegroundColor Red
    }
}

# 4. Test App Service connectivity
Write-Host "4. Testing App Service connectivity..." -ForegroundColor Yellow
try {
    $appUrl = "https://$AppServiceName.azurewebsites.net"
    $response = Invoke-WebRequest -Uri $appUrl -Method Head -TimeoutSec 30 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "   OK - App Service responding correctly" -ForegroundColor Green
    } else {
        Write-Host "   WARNING - App Service returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERROR - App Service not accessible: $_" -ForegroundColor Red
}

# 5. Test Azure CLI connectivity
Write-Host "5. Testing Azure CLI connectivity..." -ForegroundColor Yellow
try {
    $account = az account show --query "name" -o tsv 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   OK - Azure CLI connected: $account" -ForegroundColor Green
    } else {
        Write-Host "   ERROR - Azure CLI connection failed" -ForegroundColor Red
    }
} catch {
    Write-Host "   ERROR - Azure CLI test failed: $_" -ForegroundColor Red
}

# 6. Test specific deployment endpoints
Write-Host "6. Testing deployment endpoints..." -ForegroundColor Yellow
try {
    # Test SCM site connectivity
    $scmUrl = "https://$AppServiceName.scm.azurewebsites.net"
    $response = Invoke-WebRequest -Uri $scmUrl -Method Head -TimeoutSec 30 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200 -or $response.StatusCode -eq 401) {
        Write-Host "   OK - SCM site accessible" -ForegroundColor Green
    } else {
        Write-Host "   WARNING - SCM site returned status: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERROR - SCM site not accessible: $_" -ForegroundColor Red
}

# 7. Check proxy settings
Write-Host "7. Checking proxy settings..." -ForegroundColor Yellow
try {
    $proxy = [System.Net.WebRequest]::GetSystemWebProxy()
    $proxyUrl = $proxy.GetProxy("https://www.google.com")
    if ($proxyUrl.ToString() -eq "https://www.google.com") {
        Write-Host "   OK - No proxy configured" -ForegroundColor Green
    } else {
        Write-Host "   INFO - Proxy detected: $proxyUrl" -ForegroundColor Cyan
    }
} catch {
    Write-Host "   WARNING - Could not check proxy settings: $_" -ForegroundColor Yellow
}

# 8. Check firewall and antivirus
Write-Host "8. Checking potential firewall/antivirus issues..." -ForegroundColor Yellow
try {
    $processes = Get-Process | Where-Object {$_.ProcessName -like "*firewall*" -or $_.ProcessName -like "*antivirus*" -or $_.ProcessName -like "*defender*"}
    if ($processes) {
        Write-Host "   INFO - Security software detected:" -ForegroundColor Cyan
        foreach ($proc in $processes) {
            Write-Host "     - $($proc.ProcessName)" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   OK - No obvious security software detected" -ForegroundColor Green
    }
} catch {
    Write-Host "   WARNING - Could not check security software: $_" -ForegroundColor Yellow
}

# 9. Test connection timeout settings
Write-Host "9. Testing connection timeout behavior..." -ForegroundColor Yellow
try {
    $startTime = Get-Date
    $response = Invoke-WebRequest -Uri "https://management.azure.com" -Method Head -TimeoutSec 5 -ErrorAction SilentlyContinue
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    Write-Host "   INFO - Azure management endpoint response time: ${duration:F2} seconds" -ForegroundColor Cyan
    
    if ($duration -gt 3) {
        Write-Host "   WARNING - Slow connection detected" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ERROR - Connection timeout test failed: $_" -ForegroundColor Red
}

Write-Host "`n=== NETWORK DIAGNOSTIC COMPLETED ===" -ForegroundColor Green

# Recommendations based on findings
Write-Host "`nRECOMMENDATIONS:" -ForegroundColor Yellow
Write-Host "1. If basic connectivity fails: Check your internet connection" -ForegroundColor Yellow
Write-Host "2. If DNS fails: Check DNS settings or try using 8.8.8.8" -ForegroundColor Yellow
Write-Host "3. If Azure endpoints fail: Check firewall/proxy settings" -ForegroundColor Yellow
Write-Host "4. If SCM site fails: App Service may be down or misconfigured" -ForegroundColor Yellow
Write-Host "5. If slow connections: Consider using Git deployment method" -ForegroundColor Yellow
Write-Host "6. If proxy detected: Configure Azure CLI to use proxy" -ForegroundColor Yellow
Write-Host "7. For persistent issues: Try deploying from Azure Portal" -ForegroundColor Yellow 