# ============================================================
# ShellIA - AppVeyor Deploy Script
# ============================================================
# Variables AppVeyor à configurer dans les Settings du projet :
#   DOCKER_USER  : identifiant Docker Hub  (secret)
#   DOCKER_PASS  : mot de passe Docker Hub (secret)
# ============================================================

$imageName   = "gaelgael5/shellia"
$taggedImage = $imageName + ':' + $env:APPVEYOR_BUILD_VERSION
$latestImage = $imageName + ':latest'

$ErrorActionPreference = 'Stop'

Write-Host "================================================"
Write-Host " Deploying ShellIA to Docker Hub"
Write-Host " Image   : $taggedImage"
Write-Host "================================================"

# Vérifier que les credentials Docker Hub sont définis
if (-not $env:DOCKER_USER -or -not $env:DOCKER_PASS) {
  Write-Host "⚠️  DOCKER_USER ou DOCKER_PASS non défini — déploiement ignoré."
  exit 0
}

# Connexion Docker Hub
Write-Host ""
Write-Host "▶ docker login..."
"$env:DOCKER_PASS" | docker login --username "$env:DOCKER_USER" --password-stdin

# Push de l'image versionnée
Write-Host ""
Write-Host "▶ Push $taggedImage"
docker push $taggedImage

# Push du tag latest (uniquement sur la branche main)
if ($env:APPVEYOR_REPO_BRANCH -eq "main") {
  Write-Host "▶ Push $latestImage (branche main)"
  docker push $latestImage
} else {
  Write-Host "ℹ️  Branche $($env:APPVEYOR_REPO_BRANCH) — tag latest ignoré"
}

Write-Host ""
Write-Host "✅ Déploiement terminé"
Write-Host "   Image disponible : https://hub.docker.com/r/gaelgael5/shellia"
