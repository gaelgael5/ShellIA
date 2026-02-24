# ShellIA - AppVeyor Build Script
$imageName   = "blackbeardteam/shellia"
$taggedImage = $imageName + ':' + $env:APPVEYOR_BUILD_VERSION
$latestImage = $imageName + ':latest'
$ErrorActionPreference = 'Stop'
Write-Host "▶ Building $taggedImage"
docker info
docker build --tag $latestImage .
docker tag $latestImage $taggedImage
Write-Host "✅ Build OK"
docker images | Where-Object { $_ -match "shellia" }
