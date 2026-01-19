<#
PowerShell helper to set up repository protections and basic automation for acb_link_desktop.

What it does:
- Verifies `gh` is installed and you're authenticated.
- Ensures the organization `maintainers` team exists and adds specified owners (default: accesswatch, payown).
- Renames `.github/workflows/*.yml.txt` -> `.github/workflows/*.yml` so Actions run.
- Prompts for status-check contexts (defaults to `Tests, lint`) and applies branch protection to `main`:
  - require PR reviews, require CODEOWNERS reviews, 1 approving review
  - enforce linear history
  - enforce admins
  - restrict pushes to the `maintainers` team
- Adds simple `.github/dependabot.yml`, `SECURITY.md`, and `CODE_OF_CONDUCT.md` if they don't exist.

Usage: run from repository root in PowerShell:
  powershell -ExecutionPolicy Bypass -File .\scripts\setup_repo_protection.ps1

Note: this script uses `gh` and `curl`/`Invoke-RestMethod`. You must run `gh auth login` first and have org/admin rights.
#>
param(
    [string]$Owner = "acbnational",
    [string]$Repo = "acb_link_desktop",
    [string]$Branch = "main",
    [string[]]$Owners = @("accesswatch","payown"),
    [string]$TeamName = "maintainers"
)

function FailIf([string]$msg) {
    Write-Error $msg
    exit 1
}

# Check gh
if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    FailIf "gh CLI not found. Install from https://cli.github.com/ and run 'gh auth login'."
}

# Check authentication and admin rights for repo
Write-Host "Checking GitHub authentication and repository access..."
try {
    $token = gh auth token 2>$null
} catch {
    $token = $null
}
if (-not $token) {
    FailIf "No gh auth token found. Run 'gh auth login' first."
}

$repoApi = "repos/$Owner/$Repo"
$repoJson = gh api $repoApi | ConvertFrom-Json
if (-not $repoJson.permissions.admin) {
    Write-Warning "Your account does not appear to have admin permission on $Owner/$Repo. Repo admin rights are required for some operations."
    $answer = Read-Host "Continue anyway? (y/N)"
    if ($answer -notin @('y','Y')) { FailIf "Aborting - insufficient permissions." }
}

# Ensure team exists
Write-Host "Ensuring team '$TeamName' exists in org '$Owner'..."
$teams = gh api "/orgs/$Owner/teams" | ConvertFrom-Json
$team = $teams | Where-Object { $_.slug -eq $TeamName }
if (-not $team) {
    Write-Host "Team not found; creating..."
    gh api -X POST /orgs/$Owner/teams -f name="$TeamName" -f description="Repository maintainers" -f privacy="closed" -f permission="push" | Out-Null
    Start-Sleep -Seconds 1
    $teams = gh api "/orgs/$Owner/teams" | ConvertFrom-Json
    $team = $teams | Where-Object { $_.slug -eq $TeamName }
    if (-not $team) { FailIf "Failed to create team $TeamName" }
    Write-Host "Team created with slug: $($team.slug)"
} else {
    Write-Host "Team exists (slug: $($team.slug))."
}

# Add owners to team
foreach ($u in $Owners) {
    Write-Host "Adding user '$u' to team '$TeamName' as maintainer..."
    gh api -X PUT "/orgs/$Owner/teams/$TeamName/memberships/$u" -f role=\"maintainer\" | Out-Null
}

# Rename workflow files if needed
$workflowDir = Join-Path -Path (Get-Location) -ChildPath ".github\workflows"
if (Test-Path $workflowDir) {
    Get-ChildItem -Path $workflowDir -Filter "*.yml.txt" -File | ForEach-Object {
        $src = $_.FullName
        $dest = [IO.Path]::ChangeExtension($src, ".yml")
        if (-not (Test-Path $dest)) {
            Write-Host "Renaming $($_.Name) -> $(Split-Path $dest -Leaf)"
            Move-Item -Path $src -Destination $dest
        } else {
            Write-Host "Target $($dest) already exists; skipping rename of $($_.Name)"
        }
    }
} else {
    Write-Warning ".github\workflows directory not found in current location. Are you at the repo root?"
}

# Prompt for status check contexts
$defaultContexts = "Tests, lint"
$input = Read-Host "Enter required status check contexts (comma-separated) [default: $defaultContexts]"
if ([string]::IsNullOrWhiteSpace($input)) { $input = $defaultContexts }
$contexts = $input -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne '' }
Write-Host "Using contexts: $($contexts -join ', ')"

# Build branch protection payload
$payload = @{
    required_status_checks = @{ strict = $true; contexts = $contexts }
    enforce_admins = $true
    required_pull_request_reviews = @{ dismiss_stale_reviews = $true; require_code_owner_reviews = $true; required_approving_review_count = 1 }
    enforce_linear_history = @{ enabled = $true }
    restrictions = @{ users = @(); teams = @($TeamName) }
}

$json = $payload | ConvertTo-Json -Depth 10

# Apply branch protection using GitHub REST API via Invoke-RestMethod
$uri = "https://api.github.com/repos/$Owner/$Repo/branches/$Branch/protection"
$headers = @{ Authorization = "token $token"; Accept = "application/vnd.github+json"; 'X-GitHub-Api-Version' = '2022-11-28' }
Write-Host "Applying branch protection to $Branch..."
try {
    $resp = Invoke-RestMethod -Method Put -Uri $uri -Headers $headers -Body $json -ContentType 'application/json'
    Write-Host "Branch protection applied successfully."
} catch {
    Write-Warning "Failed to apply branch protection: $($_.Exception.Message)"
    Write-Host "Response:`n$($_.Exception.Response | Out-String)"
}

# Helper to create file via GitHub contents API if missing
function Ensure-RepoFile([string]$path, [string]$content, [string]$commitMessage) {
    $encPath = $path -replace " ", "%20"
    Write-Host "Checking for $path in repository..."
    $exists = $false
    try {
        gh api "/repos/$Owner/$Repo/contents/$encPath" | Out-Null
        $exists = $true
    } catch {
        $exists = $false
    }
    if ($exists) {
        Write-Host "$path already exists; skipping."
        return
    }
    $b64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($content))
    Write-Host "Creating $path in repository..."
    gh api -X PUT "/repos/$Owner/$Repo/contents/$encPath" -f message="$commitMessage" -f content="$b64" -f branch="$Branch" | Out-Null
    Write-Host "$path created (committed to $Branch)."
}

# Add Dependabot config
$dependabotContent = @"
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
"@
Ensure-RepoFile ".github/dependabot.yml" $dependabotContent "Add dependabot config"

# Add SECURITY.md
$securityContent = @"
# Security

Report security issues at security@acb.org (or use GitHub Security Advisories).
"@
Ensure-RepoFile "SECURITY.md" $securityContent "Add SECURITY.md"

# Add CODE_OF_CONDUCT.md (simple template)
$codeOfConduct = @"
# Code of Conduct

Be respectful. Please follow community standards when contributing.
"@
Ensure-RepoFile "CODE_OF_CONDUCT.md" $codeOfConduct "Add CODE_OF_CONDUCT.md"

Write-Host "
Summary:
- Team ensured: $TeamName
- Owners added: $($Owners -join ', ')
- Workflows renamed where needed in .github/workflows
- Branch protection attempted for branch: $Branch
- Created .github/dependabot.yml, SECURITY.md, CODE_OF_CONDUCT.md if they were missing
"
Write-Host "Done. Verify changes on GitHub and adjust contexts or protection settings as needed."
git add .
git commit -m "chore: fix lint errors and apply formatting"
Made changes.
