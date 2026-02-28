param(
  [ValidateSet("pre-commit","pre-push")][string]$Mode = "pre-commit"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg){
  Write-Error $msg
  exit 1
}

if($Mode -eq "pre-commit"){
  $files = git diff --cached --name-only
} else {
  $up = git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>$null
  if([string]::IsNullOrWhiteSpace($up)){
    $files = git diff --cached --name-only
  } else {
    $files = git diff --name-only "$up..HEAD"
  }
}

if($null -eq $files){ exit 0 }
if($files -is [string]){ $files = @($files) }

$blockRegex = @(
  '^infield/ai_save/items/',
  '^infield/ai_save/index\.csv$',
  '^infield/ai_save/decisions/decisions\.csv$',
  '^secrets/',
  '^keys/private/',
  '^governance/keys/',
  '\.db$',
  '\.sqlite$',
  '\.pem$',
  '\.key$',
  '\.pfx$',
  '\.p12$'
)

$allowExact = @(
  'infield/ai_save/specs/index.schema.csv',
  'infield/ai_save/specs/decisions.schema.csv',
  'infield/ai_save/specs/AI_SAVE_SPEC_v0.1.md',
  'infield/ai_save/bin/ai_decide.ps1',
  'infield/ai_save/bin/ai_save_clip.ps1',
  'infield/ai_save/bin/git_guard_check.ps1'
)

$violations = @()

foreach($f in $files){
  if([string]::IsNullOrWhiteSpace($f)){ continue }
  if($allowExact -contains $f){ continue }
  foreach($rx in $blockRegex){
    if($f -match $rx){
      $violations += $f
      break
    }
  }
}

if($violations.Count -gt 0){
  $list = ($violations | Sort-Object -Unique) -join "`n"
  Fail ("Blocked by git guard (" + $Mode + "). Remove from staging / commits:`n" + $list)
}

exit 0
