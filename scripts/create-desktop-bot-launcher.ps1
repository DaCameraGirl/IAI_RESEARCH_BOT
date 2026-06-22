# Creates desktop shortcut with Research Genie icon
$repo = Split-Path $PSScriptRoot -Parent
$desktop = [Environment]::GetFolderPath('Desktop')
$icon = Join-Path $repo 'assets\genie-mascot.ico'
$target = Join-Path $repo 'Launch RWS Research Bot.bat'
$shortcut = Join-Path $desktop 'RWS Research Bot.lnk'

if (-not (Test-Path $icon)) {
    python (Join-Path $repo 'scripts\build_genie_icon.py')
}

$wsh = New-Object -ComObject WScript.Shell
$link = $wsh.CreateShortcut($shortcut)
$link.TargetPath = $target
$link.WorkingDirectory = $repo
$link.WindowStyle = 1
$link.Description = 'RWS Research Genie — deep hunt, burn-check, draft candidates'
$link.IconLocation = "$icon,0"
$link.Save()

Write-Host "Desktop shortcut: $shortcut"
Write-Host "Icon: $icon"