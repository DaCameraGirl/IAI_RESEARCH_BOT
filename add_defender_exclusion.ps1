# Add Windows Defender exclusion for RWS Research Bot
# Run as Administrator

$RepoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistPath = Join-Path $RepoPath "dist"

Write-Host "Adding Windows Defender exclusion..." -ForegroundColor Cyan

try {
    # Add exclusion for the dist folder
    Add-MpPreference -ExclusionPath $DistPath
    Write-Host "✅ Exclusion added: $DistPath" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now try running the .exe or .bat file again!" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Failed to add exclusion. You need to run this as Administrator." -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell → Run as Administrator, then run:" -ForegroundColor Yellow
    Write-Host "  cd '$RepoPath'" -ForegroundColor White
    Write-Host "  .\add_defender_exclusion.ps1" -ForegroundColor White
}
