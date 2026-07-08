$desktop = [Environment]::GetFolderPath('Desktop')
$repo = 'C:\Users\enter\OneDrive\Desktop\RWS_RESEARCHER'

$links = @(
    @{ Name = '26052 Blender Offset Blades'; Target = Join-Path $repo '26052_Rechargeable_Blender_Offset_Blades'; Color = 'purple' }
    @{ Name = '25974 Oximidol'; Target = Join-Path $repo '25974_Oximidol'; Color = 'blue' }
    @{ Name = '26005 Hymn Cebuano'; Target = Join-Path $repo '26005_Hymn_Research_Cebuano'; Color = 'green' }
    @{ Name = '26006 Hymn Russian'; Target = Join-Path $repo '26006_Hymn_Research_Russian'; Color = 'orange' }
    @{ Name = '26016 Hymn Italian'; Target = Join-Path $repo '26016_Hymn_Research_Italian'; Color = 'red' }
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