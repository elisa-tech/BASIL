#!/bin/bash

source .env
source ./common.sh

# Settings
DB_USER="basil-admin"
DB_NAME="basil"
DB_PASSWORD="${BASIL_DB_PASSWORD=-your_secure_password}"
RESET_CLUSTERS="${BASIL_RESET_POSTGRES_CLUSTERS=-0}"
TESTING="${BASIL_TESTING:-0}"

if [ "$TESTING" = "1" ]; then
    DB_NAME="test"
fi

set -e

echo
echo ===================================================================
echo BASIL Database initialization: ${DB_NAME}
echo -------------------------------------------------------------------

# Choose a safe working directory, e.g., /tmp or your home directory
WORKDIR="/tmp"

pushd "$WORKDIR" >/dev/null

# Check if postgres is installed
install_package postgresql
install_package postgresql-contrib

# Start and enable PostgreSQL service
echo "Starting and enabling postgresql service..."
systemctl start postgresql
systemctl enable postgresql

if [ "$RESET_CLUSTERS" -eq 1 ]; then

  echo "🔍 Detecting installed PostgreSQL version..."

  # Step 1: Detect installed PostgreSQL version
  PG_VERSION=$(ls /usr/lib/postgresql 2>/dev/null | grep -E '^[0-9]+$' | sort -V | tail -n1)

  if [ -z "$PG_VERSION" ]; then
    echo "❌ No PostgreSQL version installed."
    exit 1
  fi

  echo "✅ PostgreSQL version detected: $PG_VERSION"

  # Step 2: Drop all existing clusters (if any)
  echo "🧹 Dropping all existing clusters..."
  while read -r version cluster_name _; do
  if [[ "$version" =~ ^[0-9]+$ && "$cluster_name" != "Cluster" ]]; then
    echo "⚠️  Dropping cluster: $version/$cluster_name"
    pg_dropcluster --stop "$version" "$cluster_name"
  fi
  done < <(pg_lsclusters)

  # Step 3: Create a new default cluster
  echo "🛠 Creating new cluster: ${PG_VERSION}/main"
  pg_createcluster "$PG_VERSION" main --start --port=5432

  # Step 4: Verify
  echo "📋 Cluster list after recreation:"
  pg_lsclusters

  # Optional: enable the service
  systemctl enable --now postgresql

  echo "✅ PostgreSQL is reset with a fresh cluster on port 5432."
fi

# Find the postgresql.conf location
PG_CONF=$(sudo -u postgres psql -t -P format=unaligned -c "SHOW config_file;")
echo "postgresql.conf found at: $PG_CONF"

# Backup postgresql.conf before editing
cp "$PG_CONF" "${PG_CONF}.bak_$(date +%Y%m%d_%H%M%S)"

# Ensure listen_addresses is set to '*'
sed -i "s/^#*\s*listen_addresses\s*=.*/listen_addresses = '*'/" "$PG_CONF"

# Ensure port is set to 5432
if grep -q "^port\s*=" "$PG_CONF"; then
  sed -i "s/^port\s*=.*/port = 5432/" "$PG_CONF"
else
  echo "port = 5432" | tee -a "$PG_CONF" > /dev/null
fi

echo "Configuration updated. Restarting PostgreSQL..."
systemctl restart postgresql

echo "PostgreSQL installed, configured, and running on port 5432."

# Create user if it doesn't exist
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE USER \"${DB_USER}\" WITH PASSWORD '${DB_PASSWORD}';"

# Create database if it doesn't exist
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
  sudo -u postgres psql -c "CREATE DATABASE \"${DB_NAME}\" OWNER \"${DB_USER}\";"

# Grant privileges
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE \"${DB_NAME}\" TO \"${DB_USER}\";"

popd >/dev/null

echo "✅ PostgreSQL user '${DB_USER}' and database '${DB_NAME}' are set up."
