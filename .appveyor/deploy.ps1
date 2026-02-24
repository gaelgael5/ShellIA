# ShellIA - AppVeyor Deploy Script
$imageName   = "blackbeardteam/shellia"
$taggedImage = $imageName + ':' + $env:APPVEYOR_BUILD_VERSION
$latestImage = $imageName + ':latest'
$ErrorActionPreference = 'Stop'
Write-Host "▶ Deploy $taggedImage -> Docker Hub"
if (-not $env:DOCKER_USER -or -not $env:DOCKER_PASS) { Write-Host "⚠️ Credentials manquants."; exit 0 }
"$env:DOCKER_PASS" | docker login --username "$env:DOCKER_USER" --password-stdin
docker push $taggedImage
if ($env:APPVEYOR_REPO_BRANCH -eq "main") {
  docker push $latestImage
  Write-Host "✅ Pushed $latestImage"
}
Write-Host "✅ Deploy OK → https://hub.docker.com/r/blackbeardteam/shellia"
