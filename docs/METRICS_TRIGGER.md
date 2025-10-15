# METRICS_TRIGGER endpoint — enabling and deployment guidance

This project exposes a development-only endpoint at `/metrics/trigger/` that
allows incrementing in-process metrics for debugging. The endpoint is intentionally
hidden unless a secret token is configured.

How it works
-----------
- The endpoint requires a header `X-METRICS-TRIGGER-TOKEN` matching the
  `METRICS_TRIGGER_TOKEN` setting. If the setting is empty, the endpoint returns
  `404` (hidden).
- The endpoint also restricts access to localhost by default.

Security guidance
-----------------
- Do NOT set `METRICS_TRIGGER_TOKEN` in public repositories. Use your secret
  manager (GitHub Secrets, Vault, AWS Secrets Manager) to store the token.
- In production, prefer deleting the endpoint entirely. If you must keep it,
  ensure the token is present and only expose the service to trusted networks.

CI / Pre-deploy check
---------------------
We recommend failing the production deployment if `METRICS_TRIGGER_TOKEN` is not
configured. Example workflows and local checks are provided in the repository.

Local usage
-----------
1. Set the environment variable (or secrets manager) for your environment. Example:

PowerShell:

```powershell
$env:METRICS_TRIGGER_TOKEN = 'your-secret-token'
```

bash:

```bash
export METRICS_TRIGGER_TOKEN='your-secret-token'
```

2. Call the endpoint locally with the header:

PowerShell:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/metrics/trigger/ -Method POST -Headers @{ 'X-METRICS-TRIGGER-TOKEN' = $env:METRICS_TRIGGER_TOKEN }
```

Or with curl (Linux/macOS):

```bash
curl -X POST http://localhost:8000/metrics/trigger/ -H "X-METRICS-TRIGGER-TOKEN: $METRICS_TRIGGER_TOKEN"
```

Removing the endpoint
---------------------
To remove the endpoint entirely before deploying to production, delete the
`path('metrics/trigger/', ...)` line in `config/urls.py` and remove the
`metrics_trigger` function in `config/metrics.py`.
