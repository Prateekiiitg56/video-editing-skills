# video-editing-skills installer for Windows PowerShell 5.1+ / PowerShell 7
#
# One command:
#   irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1 | iex
# With options (pack, single skills, agent, project-local):
#   & ([scriptblock]::Create((irm https://raw.githubusercontent.com/Prateekiiitg56/video-editing-skills/main/install.ps1))) -Pack reels
#   & ([scriptblock]::Create((irm .../install.ps1))) -Skills style-cinematic,color-grading -Agent codex
#   & ([scriptblock]::Create((irm .../install.ps1))) -List
param(
    [string]$Pack = "all",
    [string[]]$Skills = @(),
    [ValidateSet("claude", "codex", "gemini", "opencode", "cursor", "agents", "all")][string]$Agent = "claude",
    [switch]$Project,
    [switch]$List,
    [switch]$Uninstall,
    [switch]$Deps,
    [string]$Source = "",
    [string]$Repo = "Prateekiiitg56/video-editing-skills",
    [string]$Branch = "main"
)
$ErrorActionPreference = "Stop"

# 1. repository source: local checkout next to this script, -Source, or download zip
if (-not $Source) {
    if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot "packs\all.txt"))) { $Source = $PSScriptRoot }
    else {
        $tmp = Join-Path ([IO.Path]::GetTempPath()) ("ves_" + [guid]::NewGuid().ToString("N"))
        New-Item -ItemType Directory -Path $tmp | Out-Null
        $zip = Join-Path $tmp "repo.zip"
        Write-Host "Downloading $Repo@$Branch ..."
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -UseBasicParsing "https://codeload.github.com/$Repo/zip/refs/heads/$Branch" -OutFile $zip
        Expand-Archive $zip -DestinationPath $tmp
        $Source = (Get-ChildItem $tmp -Directory | Select-Object -First 1).FullName
    }
}
$skillsDir = Join-Path $Source "skills"
if (-not (Test-Path $skillsDir)) { throw "skills folder not found in $Source" }

if ($List) {
    Write-Host "Packs:"
    Get-ChildItem (Join-Path $Source "packs") -Filter *.txt | ForEach-Object {
        "  {0,-11} {1}" -f $_.BaseName, ((Get-Content $_.FullName) -join " ")
    }
    Write-Host "`nSkills:"
    Get-ChildItem $skillsDir -Directory | ForEach-Object {
        $d = (Select-String -Path (Join-Path $_.FullName "SKILL.md") -Pattern "^description: (.*)" | Select-Object -First 1).Matches[0].Groups[1].Value
        "  {0,-26} {1}..." -f $_.Name, $d.Substring(0, [Math]::Min(90, $d.Length))
    }
    return
}

# 2. skill list
if ($Skills.Count -gt 0) {
    $names = @($Skills | ForEach-Object { $_ -split "," } | Where-Object { $_ })
    if ($names -notcontains "video-editing") { $names = @("video-editing") + $names }
}
else {
    $packFile = Join-Path $Source "packs\$Pack.txt"
    if (-not (Test-Path $packFile)) { throw "unknown pack '$Pack'. Packs: all core reels cinematic motion youtube commercial vfx resolve" }
    $names = @(Get-Content $packFile | Where-Object { $_.Trim() })
}

# 3. target folders
$base = if ($Project) { (Get-Location).Path } else { $HOME }
function Get-Targets([string]$a) {
    switch ($a) {
        "claude" { @(Join-Path $base ".claude\skills") }
        "codex" { @(Join-Path $base ".codex\skills") }
        "gemini" { @(Join-Path $base ".gemini\skills") }
        "opencode" { if ($Project) { @(Join-Path $base ".opencode\skills") } else { @(Join-Path $HOME ".config\opencode\skills") } }
        "cursor" { @(Join-Path $base ".cursor\skills") }
        "agents" { @(Join-Path $base ".agents\skills") }
        "all" { foreach ($x in "claude", "codex", "gemini", "opencode", "cursor", "agents") { Get-Targets $x } }
    }
}

$count = 0
foreach ($t in (Get-Targets $Agent)) {
    New-Item -ItemType Directory -Force -Path $t | Out-Null
    foreach ($n in $names) {
        $n = $n.Trim()
        $src = Join-Path $skillsDir $n
        if (-not (Test-Path $src)) { Write-Warning "unknown skill: $n"; continue }
        $dst = Join-Path $t $n
        if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
        if ($Uninstall) { Write-Host "  - $dst"; continue }
        Copy-Item -Recurse $src $dst
        $count++
    }
    if (-not $Uninstall) { Write-Host "Installed into $t" }
}

if (-not $Uninstall) {
    Write-Host "Done: $count skill copies. Restart your agent, then ask e.g. 'edit this into an Instagram reel'."
    if ($Deps) {
        Write-Host "Installing Python helpers..."
        python -m pip install --user numpy scipy opencv-python librosa soundfile pillow pyloudnorm
    }
    if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
        Write-Host "Note: ffmpeg not found on PATH. Install it with: winget install Gyan.FFmpeg"
    }
}
