# run_night.ps1 — orchestratore del job notturno (chiamato da Task Scheduler).
# Blinda standby -> esegue night_runner -> ripristina standby. Logga tutto.
$ErrorActionPreference = "Continue"
$pkg = "$env:USERPROFILE\amazon_search"
$log = "$env:USERPROFILE\amazon_search_out\run_night.log"
New-Item -ItemType Directory -Force (Split-Path $log) | Out-Null

function Log($m) { "$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))  $m" | Tee-Object -FilePath $log -Append }

Log "=== START run_night ==="
& "$pkg\blinda.ps1"                      # standby/hibernate/lid OFF su AC
Log "standby blindato"

# night_runner: legge queries.txt, retry+resume+budget. --specs +crediti Canopy.
$py = (Get-Command python).Source
Log "python: $py"
& $py "$pkg\night_runner.py" --specs *>> $log
Log "night_runner finito (exit $LASTEXITCODE)"

& "$pkg\blinda.ps1" -Restore               # ripristina sleep normale
Log "standby ripristinato"
Log "=== END run_night ==="
