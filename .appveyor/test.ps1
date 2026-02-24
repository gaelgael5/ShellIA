# ShellIA - AppVeyor Test Script
$imageName     = "blackbeardteam/shellia"
$latestImage   = $imageName + ':latest'
$containerName = "shellia__test"
$ErrorActionPreference = 'SilentlyContinue'
if ($env:ARCH -ne "amd64") { Write-Host "Skip."; exit 0 }
docker kill $containerName 2>$null; docker rm -f $containerName 2>$null
$ErrorActionPreference = 'Stop'
docker run --name $containerName -d -p 18000:8000 -e SECRET_KEY=test-key-ci -e SHELLIA_ENV=local $latestImage
Write-Host "⏳ Attente 15s..."; Start-Sleep 15
docker logs $containerName
$ok = $false
for ($i=0; $i -lt 5; $i++) {
  try {
    $r = Invoke-WebRequest -Uri "http://localhost:18000/auth/config" -TimeoutSec 5 -UseBasicParsing
    if ($r.StatusCode -eq 200) { Write-Host "✅ Healthcheck OK"; $ok = $true; break }
  } catch { Start-Sleep 5 }
}
$ErrorActionPreference = 'SilentlyContinue'
docker kill $containerName; docker rm -f $containerName
if (-not $ok) { Write-Host "❌ Healthcheck KO"; exit 1 }
Write-Host "✅ Tests OK"
