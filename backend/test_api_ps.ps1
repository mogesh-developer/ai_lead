$URI = "http://localhost:5000/api/save-extracted-leads"
$Headers = @{"Content-Type" = "application/json"}
$Body = @{
    leads = @(
        @{
            name = "Test Developer"
            email = "test.dev@company.com"
            company = "Test Company"
            phone = "+1-555-0001"
            position = "Developer"
        }
    )
} | ConvertTo-Json

Write-Host "Testing API endpoint: $URI"
Write-Host "Payload: $Body`n"

try {
    $Response = Invoke-WebRequest -Uri $URI -Method POST -Headers $Headers -Body $Body -UseBasicParsing
    Write-Host "Status Code: $($Response.StatusCode)"
    Write-Host "Response:`n$($Response.Content)"
} catch {
    Write-Host "Error: $_"
    if ($_.Exception.Response) {
        Write-Host "Response: $($_.Exception.Response | ConvertFrom-Json)"
    }
}
