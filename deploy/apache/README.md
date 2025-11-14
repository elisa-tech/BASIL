### BASIL Apache deployment

This folder contains helper scripts to deploy BASIL (API + Frontend) behind Apache on a Debian/Ubuntu host.

Scripts expect configuration via a local `.env` file, then you run `run.sh` to provision PostgreSQL, build and configure the API (mod_wsgi) and the frontend under Apache.

---

### Prerequisites

- Run on a Debian/Ubuntu system with `systemd` and `apt`.
- A user with sudo privileges and outbound Internet access.
- Open TCP ports for the API and APP (defaults: 5000 and 9000).

The scripts will install required packages (Apache, PostgreSQL, Python, Node toolchain) if missing.

---

### Configure .env

It is sourced by bash, so stick to `KEY=VALUE` and use quotes if values contain spaces.

Required/commonly used variables:

- BASIL_SERVER_NAME: public hostname or IP used in Apache vhosts
- BASIL_SERVER_ALIAS: optional additional host alias
- BASIL_SERVER_ADMIN: admin email for Apache configs
- BASIL_API_PORT: API Apache vhost port (default 5000)
- BASIL_APP_PORT: Frontend Apache vhost port (default 9000)
- BASIL_ADMIN_PASSWORD: password of BASIL admin user created by default
- BASIL_DB_PASSWORD: PostgreSQL user password used during DB init
- BASIL_TESTING: 1 to use a `test` DB instead of `basil` (default 0)
- BASIL_TEST_RUNS_BASE_DIR: base dir for tmt test runs (default `/var/basil/test-runs`)
- BASIL_GITCLONE: 1 = force fresh clone to `/tmp/basil`, 0 = reuse if present (default 1)
- BASIL_GITGOBACK: number of commits to revert from HEAD (default 0)
- BASIL_COMMITBEFORE: ISO8601 date used only when `BASIL_GITGOBACK < 0` (e.g. `2025-01-01 00:00:00 +0000`)
- BASIL_RESET_POSTGRES_CLUSTERS: 1 to wipe/recreate all local Postgres clusters (DANGEROUS), 0 or -1 to skip (default)

Example `.env` you can copy and adjust:

```bash
# Apache vhost details
BASIL_SERVER_NAME="your.host.name"
BASIL_SERVER_ALIAS="your.host.alias"
BASIL_SERVER_ADMIN="admin@example.com"

# Ports
BASIL_API_PORT=5000
BASIL_APP_PORT=9000

# BASIL runtime
BASIL_ADMIN_PASSWORD="ChangeMe_Strong_Admin_Password"
BASIL_TEST_RUNS_BASE_DIR="/var/basil/test-runs"
BASIL_TESTING=0

# Database
BASIL_DB_PASSWORD="ChangeMe_Strong_DB_Password"
BASIL_RESET_POSTGRES_CLUSTERS=-1

# Git checkout behavior for building
BASIL_GITCLONE=1
BASIL_GITGOBACK=0
# Only used if BASIL_GITGOBACK < 0
BASIL_COMMITBEFORE="2025-01-01 00:00:00 +0000"
```

Notes:
- Passwords are required: set both `BASIL_ADMIN_PASSWORD` and `BASIL_DB_PASSWORD`.
- Use quotes for values with special characters.

---

### Run the deployment

From this folder:

```bash
sudo ./run.sh
```

Why sudo? The scripts write under `/var/www`, `/etc/apache2`, manage services, and change ownership to `www-data`.

What `run.sh` does:
- Installs required packages via apt
- Initializes PostgreSQL (`init_postgresql.sh`)
- Builds and configures the API for Apache/mod_wsgi (`build_basil_api.sh`)
- Builds the frontend, configures Apache static vhost with React router rewrite (`build_basil_frontend.sh`)

Artifacts and logs in this folder:
- `init_postgresql.log`
- `build_basil_api.log`
- `build_basil_frontend.log`

---

### Verify

- API version endpoint: `http://<BASIL_SERVER_NAME>:<BASIL_API_PORT>/version`
- Frontend version: `http://<BASIL_SERVER_NAME>:<BASIL_APP_PORT>/version`

Both checks are executed automatically at the end of the respective scripts and reported in the logs.

---

### Troubleshooting

- Ports already in use: adjust `BASIL_API_PORT` / `BASIL_APP_PORT` in `.env` and re-run.
- Wrong hostname: update `BASIL_SERVER_NAME` (and optional alias) and re-run.
- PostgreSQL reset: set `BASIL_RESET_POSTGRES_CLUSTERS=1` only if you understand it will drop existing clusters.
- Rebuild from a clean checkout: set `BASIL_GITCLONE=1`.
