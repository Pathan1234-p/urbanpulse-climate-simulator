# Deploy UrbanPulse to GitHub (run after: gh auth login)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + `
            [System.Environment]::GetEnvironmentVariable("Path", "User")

gh auth status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run: gh auth login" -ForegroundColor Yellow
    exit 1
}

$repoName = "urbanpulse-climate-simulator"
$view = gh repo view "Pathan1234-p/$repoName" 2>&1
if ($LASTEXITCODE -ne 0) {
    gh repo create $repoName --public --source=. --remote=origin --description "Pune PMC urban heat risk and sustainability climate simulator" --push
} else {
    git push -u origin main
}

Write-Host "`nDone! Repository:" -ForegroundColor Green
gh repo view --web
