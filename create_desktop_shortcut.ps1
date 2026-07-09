# Create desktop shortcut for RWS Research Bot with genie icon

$WshShell = New-Object -ComObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "RWS Research Bot.lnk"

$RepoPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExePath = Join-Path $RepoPath "dist\RWS_Research_Bot.exe"
$IconPath = Join-Path $RepoPath "assets\genie-mascot.ico"

# Create shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $ExePath
$Shortcut.WorkingDirectory = $RepoPath
$Shortcut.IconLocation = $IconPath
$Shortcut.Description = "RWS Research Bot - Your bottled research genie"
$Shortcut.Save()

Write-Host "✅ Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host "🧞 Icon: Genie mascot" -ForegroundColor Cyan
