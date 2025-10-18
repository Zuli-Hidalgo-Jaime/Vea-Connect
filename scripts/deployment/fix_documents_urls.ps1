# Simple script to diagnose documents URL issues
param(
    [string]$ResourceGroup = "vea-connect-rg",
    [string]$WebAppName = "vea-connect-g5dje9eba9bscnb6"
)

Write-Host "URL DIAGNOSTIC FOR DOCUMENTS" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Check Azure CLI
try {
    $azVersion = az version --output json | ConvertFrom-Json
    Write-Host "Azure CLI detected: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "Azure CLI not installed" -ForegroundColor Red
    exit 1
}

# Check login
try {
    $account = az account show --output json | ConvertFrom-Json
    Write-Host "Connected as: $($account.user.name)" -ForegroundColor Green
} catch {
    Write-Host "Not logged in. Run: az login" -ForegroundColor Red
    exit 1
}

Write-Host "Starting SSH session to Azure App Service..." -ForegroundColor Yellow
Write-Host "You will be connected to the remote shell. Run these commands manually:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Check URL files:" -ForegroundColor Cyan
Write-Host "   cd /home/site/wwwroot" -ForegroundColor White
Write-Host "   ls -la apps/documents/urls.py" -ForegroundColor White
Write-Host "   cat apps/documents/urls.py" -ForegroundColor White
Write-Host ""
Write-Host "2. Check templates:" -ForegroundColor Cyan
Write-Host "   find . -name documents.html" -ForegroundColor White
Write-Host "   find . -name base_dashboard.html" -ForegroundColor White
Write-Host ""
Write-Host "3. Check Django config:" -ForegroundColor Cyan
Write-Host "   python -c 'from django.conf import settings; print([app for app in settings.INSTALLED_APPS if \"documents\" in app])'" -ForegroundColor White
Write-Host ""
Write-Host "4. Test URL resolution:" -ForegroundColor Cyan
Write-Host "   python -c 'from django.urls import reverse; print(reverse(\"documents:document_list\"))'" -ForegroundColor White
Write-Host ""
Write-Host "5. Check Python imports:" -ForegroundColor Cyan
Write-Host "   python -c 'from apps.documents import urls; print(\"URLs imported\")'" -ForegroundColor White
Write-Host "   python -c 'from apps.documents import views; print(\"Views imported\")'" -ForegroundColor White
Write-Host ""
Write-Host "6. Check error logs:" -ForegroundColor Cyan
Write-Host "   tail -n 20 /home/LogFiles/Application/function_*.log | grep -i documents" -ForegroundColor White
Write-Host ""
Write-Host "Press Enter to start SSH session..." -ForegroundColor Yellow
Read-Host

# Start SSH session
az webapp ssh --name $WebAppName --resource-group $ResourceGroup
