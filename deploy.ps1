<#
Deploy do backend (API Flask) para o Harbor.

Uso:
  .\deploy.ps1 -Tag stable    # producao  -> api:stable
  .\deploy.ps1 -Tag latest    # homolog   -> api:latest

O script ativa na .env o bloco DINAMICAS do ambiente correspondente (a .env
inteira e copiada para dentro da imagem pelo Dockerfile), faz o build e o push.
#>
param(
    [Parameter(Mandatory = $true, HelpMessage = 'stable = producao | latest = homologacao')]
    [ValidateSet('stable', 'latest')]
    [string]$Tag
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$envName = if ($Tag -eq 'stable') { 'Produção' } else { 'Homologação' }
$image = "harbor.sistemafiea.com.br/dataproduct-aw-plataformaunidades-api/api:$Tag"

# ---------------------------------------------------------------------------
# 1. Ativa o bloco do ambiente na .env: dentro da secao DINAMICAS, descomenta
#    as variaveis do bloco alvo e comenta as dos demais blocos.
# ---------------------------------------------------------------------------
$envFile = Join-Path $PSScriptRoot '.env'
if (-not (Test-Path $envFile)) { throw ".env nao encontrada em $PSScriptRoot" }

$currentBlock = $null
$output = foreach ($line in Get-Content $envFile -Encoding utf8) {
    $headerMatch = [regex]::Match($line, '^# --- (.+?) -{3,}')
    if ($headerMatch.Success) {
        $name = ($headerMatch.Groups[1].Value -replace '\(ATIVO\)', '').Trim()
        $currentBlock = $name
        $marker = ''
        if ($name -eq $envName) { $marker = ' (ATIVO)' }
        ("# --- $name$marker ").PadRight(79, '-')
        continue
    }

    if ($null -ne $currentBlock -and $line -match '^#?\s*[A-Za-z_][A-Za-z0-9_]*=') {
        $bare = $line -replace '^#\s*', ''
        if ($currentBlock -eq $envName) { $bare } else { "# $bare" }
        continue
    }

    $line
}

Set-Content -Path $envFile -Value $output -Encoding utf8
Write-Host "[deploy] .env ativada para: $envName" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# 2. Build e push
# ---------------------------------------------------------------------------
Write-Host "[deploy] docker build -t $image ." -ForegroundColor Cyan
# --provenance/--sbom=false: publica um manifest unico, sem os attestations
# que aparecem no Harbor como lista de artefatos OCI "unknown/unknown".
docker build --provenance=false --sbom=false -t $image .
if ($LASTEXITCODE -ne 0) { throw "docker build falhou (exit $LASTEXITCODE)" }

Write-Host "[deploy] docker push $image" -ForegroundColor Cyan
docker push $image
if ($LASTEXITCODE -ne 0) { throw "docker push falhou (exit $LASTEXITCODE)" }

Write-Host "[deploy] concluido: $image ($envName)" -ForegroundColor Green
