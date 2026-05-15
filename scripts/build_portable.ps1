param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($Clean) {
    Remove-Item -LiteralPath (Join-Path $Root "build") -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath (Join-Path $Root "dist") -Recurse -Force -ErrorAction SilentlyContinue
}

python -m s2_mod_manager.tools.write_release_metadata --output release-metadata.json
python -m PyInstaller .\Subnautica2ModManager.spec --noconfirm

$Dist = Join-Path $Root "dist\Subnautica2ModManager"
if (-not (Test-Path $Dist)) {
    throw "Expected portable dist folder was not created: $Dist"
}

Copy-Item -LiteralPath ".\README.md", ".\PRIVACY.md", ".\LICENSE", ".\release-metadata.json" -Destination $Dist -Force
Write-Host "Portable build ready: $Dist"
