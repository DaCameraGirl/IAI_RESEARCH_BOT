$desktop = [Environment]::GetFolderPath('Desktop')
$repo = 'C:\Users\enter\OneDrive\Desktop\RWS_RESEARCHER'

$links = @(
    @{ Name = '25854 Wafer Dividing'; Target = Join-Path $repo '25854_Semiconductor_Wafer_Dividing'; Color = 'blue' }
    @{ Name = '25853 LED Resin'; Target = Join-Path $repo '25853_Light_Emitting_Device_Resin_Package'; Color = 'green' }
    @{ Name = '25867 Remote Memory'; Target = Join-Path $repo '25867_Remote_Memory_Transactions'; Color = 'purple' }
)

$colorScript = Join-Path $repo 'scripts\set-study-folder-color.ps1'

foreach ($link in $links) {
    $path = Join-Path $desktop $link.Name
    if (Test-Path -LiteralPath $path) {
        $item = Get-Item -LiteralPath $path -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Remove-Item -LiteralPath $path -Force
        } else {
            Write-Warning "Skipping $($link.Name): path exists and is not a junction."
            continue
        }
    }
    New-Item -ItemType Junction -Path $path -Target $link.Target | Out-Null
    & $colorScript -FolderPath $link.Target -Color $link.Color
    Write-Host "Created junction: $path -> $($link.Target) ($($link.Color))"
}