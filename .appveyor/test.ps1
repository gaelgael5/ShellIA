# ============================================================
# ShellIA - AppVeyor Test Script
# ============================================================

$imageName     = "gaelgael5/shellia"
$latestImage   = $imageName + ':latest'
$containerName = "shellia__test"

$ErrorActionPreference = 'SilentlyContinue'

if ($env:ARCH -ne "amd64") {
  Write-Host "Arch $env:ARCH détecté — tests ignorés."
  exit 0
}

Write-Host "================================================"
Write-Host " Testing ShellIA container"
Write-Host " Image : $latestImage"
Write-Host "================================================"

# Nettoyer si un container de test existe déjà
docker kill $containerName 2>$null
docker rm -f $containerName 2>$null

$ErrorActionPreference = 'Stop'

# Démarrer le container en mode test (SECRET_KEY factice)
Write-Host ""
Write-Host "▶ Démarrage du container..."
docker run --name $containerName -d `
  -p 18000:8000 `
  -e SECRET_KEY=test-key-ci `
  -e SHELLIA_ENV=local `
  $latestImage

# Attendre que l'app démarre
Write-Host "⏳ Attente du démarrage (15s)..."
Start-Sleep 15

# Logs
Write-Host ""
Write-Host "▶ Logs du container :"
docker logs $containerName

# Test healthcheck : appeler /auth/config
Write-Host ""
Write-Host "▶ Test healthcheck HTTP..."
$ErrorActionPreference = 'SilentlyContinue'

$maxRetries = 5
$retryCount = 0
$success = $false

while ($retryCount -lt $maxRetries -and -not $success) {
  try {
    $response = Invoke-WebRequest -Uri "http://localhost:18000/auth/config" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
      Write-Host "✅ Healthcheck OK (HTTP $($response.StatusCode))"
      $success = $true
    }
  } catch {
    $retryCount++
    Write-Host "⏳ Tentative $retryCount/$maxRetries..."
    Start-Sleep 5
  }
}

# Nettoyage
$ErrorActionPreference = 'SilentlyContinue'
docker kill $containerName
docker rm -f $containerName

if (-not $success) {
  Write-Host "❌ Healthcheck échoué après $maxRetries tentatives"
  exit 1
}

Write-Host ""
Write-Host "✅ Tests terminés avec succès"
