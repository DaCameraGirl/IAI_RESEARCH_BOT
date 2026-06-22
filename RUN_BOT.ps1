# RWS Research Bot — kills stale server, starts fresh, opens browser
Set-Location $PSScriptRoot

$port = 7842
Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 800

Start-Process "http://127.0.0.1:$port"
python scripts\rws_web.py
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Failed. Run: pip install -r requirements.txt"
    Read-Host "Press Enter to close"
}