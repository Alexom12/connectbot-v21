param()
if (-not $env:METRICS_TRIGGER_TOKEN) {
    Write-Error "METRICS_TRIGGER_TOKEN is not set"
    exit 1
}
Write-Output "METRICS_TRIGGER_TOKEN is set"
