# Manual check for documents module issues
param(
    [string]$ResourceGroup = "vea-connect-rg",
    [string]$WebAppName = "vea-connect-g5dje9eba9bscnb6"
)

Write-Host "MANUAL DOCUMENTS DIAGNOSTIC" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host "Step 1: Check if documents app is in INSTALLED_APPS" -ForegroundColor Yellow
Write-Host "Run this command in Azure App Service Kudu Console:" -ForegroundColor White
Write-Host "python -c 'from django.conf import settings; print([app for app in settings.INSTALLED_APPS if \"documents\" in app])'" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 2: Check if URL file exists" -ForegroundColor Yellow
Write-Host "Run this command in Azure App Service Kudu Console:" -ForegroundColor White
Write-Host "ls -la apps/documents/urls.py" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 3: Check if templates exist" -ForegroundColor Yellow
Write-Host "Run this command in Azure App Service Kudu Console:" -ForegroundColor White
Write-Host "find . -name documents.html" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 4: Test URL resolution" -ForegroundColor Yellow
Write-Host "Run this command in Azure App Service Kudu Console:" -ForegroundColor White
Write-Host "python -c 'from django.urls import reverse; print(reverse(\"documents:document_list\"))'" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 5: Check Python imports" -ForegroundColor Yellow
Write-Host "Run this command in Azure App Service Kudu Console:" -ForegroundColor White
Write-Host "python -c 'from apps.documents import urls; print(\"URLs imported\")'" -ForegroundColor Gray
Write-Host ""

Write-Host "Step 6: Monitor logs in real time" -ForegroundColor Yellow
Write-Host "Press Enter to start log monitoring..." -ForegroundColor White
Read-Host

# Start log monitoring
az webapp log tail --name $WebAppName --resource-group $ResourceGroup
