# ============================================================
# ShellIA - AppVeyor Build Script
# ============================================================

$imageName    = "gaelgael5/shellia"
$taggedImage  = $imageName + ':' + $env:APPVEYOR_BUILD_VERSION
$latestImage  = $imageName + ':latest'

$ErrorActionPreference = 'Stop'

Write-Host "================================================"
Write-Host " Building ShellIA Docker image"
Write-Host " Image   : $taggedImage"
Write-Host " Platform: Ubuntu / amd64"
Write-Host "================================================"

# Infos Docker
docker info

# Build de l'image depuis la racine du projet
Write-Host ""
Write-Host "▶ docker build --tag $latestImage ."
docker build --tag $latestImage .

# Tag avec la version de build
Write-Host ""
Write-Host "▶ Retagging $latestImage -> $taggedImage"
docker tag $latestImage $taggedImage

Write-Host ""
Write-Host "✅ Build terminé"
docker images | Where-Object { $_ -match "shellia" }
