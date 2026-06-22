# Apply a non-yellow folder icon via desktop.ini (Windows 10/11).
# Usage: .\set-study-folder-color.ps1 -FolderPath "C:\path\to\folder" -Color blue

param(
    [Parameter(Mandatory = $true)]
    [string]$FolderPath,
    [ValidateSet('blue', 'green', 'purple', 'orange', 'red')]
    [string]$Color = 'blue'
)

$icons = @{
    blue   = 'C:\Windows\System32\imageres.dll,174'
    green  = 'C:\Windows\System32\imageres.dll,175'
    purple = 'C:\Windows\System32\imageres.dll,178'
    orange = 'C:\Windows\System32\imageres.dll,177'
    red    = 'C:\Windows\System32\imageres.dll,176'
}

if (-not (Test-Path -LiteralPath $FolderPath)) {
    throw "Folder not found: $FolderPath"
}

$iniPath = Join-Path $FolderPath 'desktop.ini'
$content = @"
[.ShellClassInfo]
IconResource=$($icons[$Color])
InfoTip=RWS study folder
"@

Set-Content -LiteralPath $iniPath -Value $content -Encoding Unicode
attrib +s +h $iniPath
attrib +r +s $FolderPath

Write-Host "Set $Color icon on $FolderPath"