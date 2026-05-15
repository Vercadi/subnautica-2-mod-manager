param(
    [string]$Version = "",
    [string]$DistPath = ".\dist\Subnautica2ModManager",
    [string]$OutputDir = ".\dist\release"
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path "."
$dist = Resolve-Path $DistPath
$metadataPath = Join-Path $dist "release-metadata.json"
if (-not (Test-Path -LiteralPath $metadataPath)) {
    throw "Missing release metadata: $metadataPath"
}

$metadata = Get-Content -LiteralPath $metadataPath -Raw | ConvertFrom-Json
if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = [string]$metadata.version
}
if ([string]::IsNullOrWhiteSpace($Version)) {
    throw "Release version is empty."
}

$required = @(
    "Subnautica2ModManager.exe",
    "README.md",
    "LICENSE",
    "PRIVACY.md",
    "release-metadata.json"
)

foreach ($relative in $required) {
    $path = Join-Path $dist $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Portable dist is missing required release file: $relative"
    }
}

$output = Join-Path $root $OutputDir
New-Item -ItemType Directory -Force -Path $output | Out-Null

$safeVersion = ($Version -replace '[^A-Za-z0-9._-]', '-')
$zipName = "Subnautica2ModManager-$safeVersion-portable.zip"
$zipPath = Join-Path $output $zipName
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory($dist, $zipPath, [System.IO.Compression.CompressionLevel]::Optimal, $true)

$zip = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
try {
    $forbidden = $zip.Entries | Where-Object {
        $_.FullName -match '(^|/)(build|data|backups|logs|\.pytest_cache|__pycache__|Mods)(/|$)' -or
        $_.FullName -match '\.log$'
    }
    if ($forbidden) {
        $sample = ($forbidden | Select-Object -First 5 | ForEach-Object { $_.FullName }) -join ", "
        throw "Release zip contains forbidden local/build content: $sample"
    }
}
finally {
    $zip.Dispose()
}

$exePath = Join-Path $dist "Subnautica2ModManager.exe"
$exeHash = Get-FileHash -LiteralPath $exePath -Algorithm SHA256
$zipHash = Get-FileHash -LiteralPath $zipPath -Algorithm SHA256
$sumsPath = Join-Path $output "SHA256SUMS.txt"
$sumLines = @(
    "$($exeHash.Hash.ToLowerInvariant())  Subnautica2ModManager/Subnautica2ModManager.exe",
    "$($zipHash.Hash.ToLowerInvariant())  $zipName"
)
Set-Content -LiteralPath $sumsPath -Value $sumLines -Encoding UTF8

[pscustomobject]@{
    Version = $Version
    ZipPath = $zipPath
    ExePath = $exePath
    Sha256SumsPath = $sumsPath
    ExeSha256 = $exeHash.Hash.ToLowerInvariant()
    ZipSha256 = $zipHash.Hash.ToLowerInvariant()
} | Format-List
