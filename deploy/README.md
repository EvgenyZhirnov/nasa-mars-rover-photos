# Delivery

Public: https://nasarover.37-27-244-205.sslip.io

Preview (password protected): https://preview.nasarover.37-27-244-205.sslip.io

## Interface changes

1. Make changes in a feature branch and open a PR. `Test and deploy / verify`
   runs Python tests, JavaScript syntax checks, Docker build and HTTP smoke checks.
   PR jobs never receive deployment credentials.
2. Merge the change into `preview` to deploy it to the protected test site.
   Only `preview` and `main` branch pushes deploy. A manual workflow run on those
   branches also deploys; other branches only run verification.
3. Check the UI on a phone. Open a PR from `preview` into `main` and merge after
   checks pass. The production site updates automatically.
4. GitHub Actions shows the deployment result. `/healthz` includes its commit SHA.

The exact tested image is saved as a GitHub artifact (7-day retention) and sent
over SSH. The VPS does not rebuild it. No registry account or registry token is
needed. Deployments serialize on the VPS; an older running deployment is not
interrupted by a newer workflow. The single app container may be unavailable for
a few seconds while being replaced. This is not a zero-downtime deployment.

## One-time setup

Install `receive.py`, `deploy.py`, and `smoke.py` root-owned in
`/usr/local/lib/nasarover/`. Create `/opt/server/apps/nasarover-delivery/{preview,production}`,
each with this directory's `compose.yml` and a mode-600 `secrets.env` containing
an independent `SESSION_SECRET`, `NASA_API_KEY`, and `TZ=Europe/Prague`.
Production binds localhost:5082, preview localhost:5083. Volumes are separate.

Use an SSH account `nasarover-ci` with a forced command:

```
restrict,command="/usr/local/lib/nasarover/receive.py" ssh-ed25519 PUBLIC_KEY
```

The account must have no Docker group membership or general sudo. Its only
sudo permission is `/usr/local/lib/nasarover/deploy.py`; this root-owned helper
validates the target, SHA, image tag, and image revision. It cannot modify Compose,
mount host directories, or execute arbitrary SSH commands. App containers run
as UID 1000 with no Linux capabilities and a read-only root filesystem.

Add GitHub Actions secret `VPS_DEPLOY_KEY` (the dedicated private key). The verified
public SSH host key is pinned in the workflow. Never use the administrator
SSH key. Configure protected environments/branch rules in GitHub as available;
workflow files alone do not enable branch protection.

## Recovery

The helper saves `state.json` and `previous.json` per environment. If startup,
revision, or smoke checks fail, it reinstates the previous image and exits with
an error so GitHub reports the failed release. Image rollback does not undo data
changes: database changes must remain backward-compatible.

For a deliberate rollback, revert the problematic commit in the corresponding
GitHub branch; CI rebuilds and deploys the reverted code. In an emergency, an
administrator can set `APP_IMAGE` from `previous.json` and run Compose in the
environment directory, then reconcile the Git branch and state files.

Before data migrations, back up the application's volume and test restoration.
Local image retention is not an offsite data backup. Keep the current and previous
images when cleaning Docker storage. Monitor disk usage; images are not pruned
automatically. The test hostname uses third-party sslip.io and can later be replaced
by an owned domain in Caddy without changing the application.
