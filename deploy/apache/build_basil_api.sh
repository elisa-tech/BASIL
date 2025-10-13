#! /bin/bash -e
## #################################################################################################
## Initial Author: Stefan Pofahl
## #################################################################################################

source .env
source ./common.sh

## --- variables -----------------------------------------------------------------------------------
SERVER_NAME="${BASIL_SERVER_NAME:-localhost}"
SERVER_ALIAS="${BASIL_SERVER_ALIAS:-localhost}"
SERVER_ADMIN="${BASIL_SERVER_ADMIN:-admin@localhost.com}"
API_PORT="${BASIL_API_PORT:-5000}"

## --- constants -----------------------------------------------------------------------------------
BASIL_REPOSITORY=https://github.com/elisa-tech/BASIL.git
BASIL_BUILD_DIR=/tmp/basil
BASIL_API=/var/www/basil-api
WSGI_SCRIPT=$BASIL_API/api/wsgi.py
BASIL_API_CONF=/etc/apache2/sites-available/basil-api.conf
VIRTUAL_ENV=/opt/virtenv
TEST_RUNS_BASE_DIR="${BASIL_TEST_RUNS_BASE_DIR:-/var/basil/test-runs}"
REFERENCEDATE01="2025-08-31 14:45:51 +0200"  # Still with sqlite-database

### --- main -------------------------------------------------------------------

# --- check if rsync is available
if ! command -v rsync &> /dev/null; then
    echo "Error: rsync is not installed, Execution terminates!"$'\n'; exit 1;
fi
echo
echo ===================================================================
echo BASIL Backend API
echo -------------------------------------------------------------------
cd ~
echo $(pwd)

clone_basil_repo_if_needed

## --- COPY local copy of repository to $BASIL_API and change to that directory ------------
if ! [ -d $BASIL_API ]; then
    mkdir -p $BASIL_API
fi

rcpdir "$BASIL_BUILD_DIR" "$BASIL_API"
cd $BASIL_API

## --- Compare Commit and Reference Date, to compare convert date to seconds since Unix epoch
epoch1=$(date -d "$COMMITDATE" +%s)
epoch2=$(date -d "$REFERENCEDATE01" +%s)
echo "*******************************************************************************************"
if (( epoch1 > epoch2 )); then
    echo "COMMITDATE: $COMMITDATE is AFTER REFERENCEDATE: " $REFERENCEDATE01
    echo "New database engine postgreSQL"
    VERSIONID=1
else
    echo "COMMITDATE: $COMMITDATE is BEFORE REFERENCEDATE: " $REFERENCEDATE01
    echo "Old data-base engine sqlite_1_7_1"
    VERSIONID=0
fi
echo "-------------------------------------------------------------------------------------------"

## --- set rights for TEST_RUN_DIRECTORY -------------------------------
if ! [ -d $TEST_RUNS_BASE_DIR ]; then
    mkdir -p $TEST_RUNS_BASE_DIR
fi
chmod -R 755 $TEST_RUNS_BASE_DIR

## --- configure directory $BASIL_API and add folder -------------------
if ! [ -d $BASIL_API/api/ssh_keys ]; then
    mkdir -p $BASIL_API/api/ssh_keys
fi
chown -R www-data:www-data $BASIL_API && chmod -R 755 $BASIL_API

## --- create content of "wsgi.py":
cd $BASIL_API/api
echo $(pwd)
echo create wsgi-pythonscript $WSGI_SCRIPT

## --- create wsgi-pythonscript $WSGI_SCRIPT ----------------------------
printf "import sys \n\
import os \n\
sys.path.insert(0, '$BASIL_API/api') \n\
import api \n\
application = api.app \n\
import logging\n\
logging.basicConfig(stream=sys.stderr)"  > $WSGI_SCRIPT

## --- create virtual python environment:
if [ -d $VIRTUAL_ENV ]; then
    echo ---  re-establish $VIRTUAL_ENV exist  ---------------------------
    rm -R $VIRTUAL_ENV
fi

## --- Create virtual environment
mkdir -p $VIRTUAL_ENV
chown -R www-data:www-data $VIRTUAL_ENV
python3 -m venv $VIRTUAL_ENV

## ---  add to path, if not yet done
if [ -d "$VIRTUAL_ENV" ] && [[ ":$PATH:" != *":$VIRTUAL_ENV:"* ]]; then
    PATH="${PATH:+"$PATH:"}$VIRTUAL_ENV"
fi
echo $PATH

## --- Install python requirements inside the virtual environment
sed -i 's/^psycopg2-binary==/psycopg2-binary>=/' $BASIL_API/requirements.txt
$VIRTUAL_ENV/bin/pip install --no-cache-dir -r $BASIL_API/requirements.txt

## --- configure folder structure:
echo --- configure folder structure:
chown -R www-data:www-data $BASIL_API/api/ssh_keys
chmod -R 750 $BASIL_API/api/ssh_keys
mkdir -p $BASIL_API/api/user-files
chmod -R 750 $BASIL_API/api/user-files
mkdir -p $BASIL_API/db/sqlite3
mkdir -p $BASIL_API/db/models
chmod -R a+rw $BASIL_API/db

## --- activate virtual python environment, important is the leading point "."
echo --- activate virtual python environment, important is the leading point "."
echo $(pwd)
. $VIRTUAL_ENV/bin/activate

## --- write BASIL-API apache2-config file:
echo --- write BASIL-API apache2-config file:
printf "<VirtualHost *:${API_PORT}> \n\
    ServerName $SERVER_NAME \n\
    ServerAlias $SERVER_ALIAS \n\
    ServerAdmin $SERVER_ADMIN \n\
    # --- WSGI - stuff:
    WSGIProcessGroup basil-api \n\
    WSGIDaemonProcess basil-api python-home=$VIRTUAL_ENV python-path=$BASIL_API user=www-data group=www-data \n\
    WSGIScriptAlias / $WSGI_SCRIPT \n\
    # ---
    <Directory \"$BASIL_API\"> \n\
        Options Indexes FollowSymLinks \n\
        AllowOverride All \n\
        Require all granted \n\
    </Directory> \n\
    # --- Logging ---
    ErrorLog \${APACHE_LOG_DIR}/error.log \n\
    CustomLog \${APACHE_LOG_DIR}/access.log combined \n\
</VirtualHost>" > $BASIL_API_CONF
echo

## --- Add port to apache configuration
add_port_to_listen "${API_PORT}"

## --- Add Environment variables in apache systemd service
APACHE_ENVVARS_FILE=/etc/apache2/envvars
# Restore previous backup
if [ -f "${APACHE_ENVVARS_FILE}.backup" ]; then
    cp "${APACHE_ENVVARS_FILE}.backup" "${APACHE_ENVVARS_FILE}"
else
    cp "${APACHE_ENVVARS_FILE}" "${APACHE_ENVVARS_FILE}.backup"
fi
echo "export BASIL_ADMIN_PASSWORD=${BASIL_ADMIN_PASSWORD}" >> "${APACHE_ENVVARS_FILE}"
echo "export BASIL_DB_PASSWORD=${BASIL_DB_PASSWORD}" >> "${APACHE_ENVVARS_FILE}"
echo "export BASIL_TESTING=${BASIL_TESTING}" >> "${APACHE_ENVVARS_FILE}"
echo "export TEST_RUNS_BASE_DIR=${TEST_RUNS_BASE_DIR}" >> "${APACHE_ENVVARS_FILE}"

# Step 3: Reload systemd and restart Apache
echo "Reloading systemd daemon..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl start apache2

## --- activate BASIL-API apache2-config file and restart apache2 server
echo --- activate BASIL-API apache2-config file
sudo a2ensite basil-api.conf
echo --- Enable wsgi module
sudo a2enmod wsgi
echo --- restart apache2 ----------------------------------------------------------------------$'\n'
sudo systemctl restart apache2
echo --- end main --- rights of folder: $BASIL_API  -------------------------------------------$'\n'
ls -ld $BASIL_API/
echo ---  $WSGI_SCRIPT  -----------------------------------------------------------------------$'\n'
cat $WSGI_SCRIPT
echo $'\n'
echo --- Testing API Version endpoint -------------------------------------------------------------$'\n'
curl -s -w "%{http_code}" -o response.json http://${SERVER_NAME}:${API_PORT}/version | grep -q "200" && jq -e 'has("version")' response.json > /dev/null && echo "Test API Version endpoint: OK" || echo "Test API Version endpoint: FAIL"
echo --- END ----------------------------------------------------------------------------------$'\n'
cd ~
