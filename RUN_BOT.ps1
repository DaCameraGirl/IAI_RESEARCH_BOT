# Double-click or run: powershell -File RUN_BOT.ps1
Set-Location $PSScriptRoot
Write-Host ""
python scripts\study_bot.py
Write-Host ""
Write-Host "Copy the AGENT COMMAND line above into Cursor chat."
Write-Host "When done: python scripts\study_bot.py advance"
Write-Host ""
Read-Host "Press Enter to close"