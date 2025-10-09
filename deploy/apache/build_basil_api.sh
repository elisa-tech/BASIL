#! /bin/bash -e
## --- variables -----------------------------------------------------------------------------------
SERVER_NAME=Your.Host.IP.Num
SERVER_ALIAS=hostname.domain.local
SERVER_ADMIN=admin.name@domaine.local
## ---
BASIL_REPOSITORY=https://github.com/elisa-tech/BASIL.git
BASIL_BUILD_DIR=/tmp/basil
BASIL_API=/var/www/basil-api
WSGI_SCRIPT=$BASIL_API/api/wsgi.py
BASIL_API_CONF=/etc/apache2/sites-available/basil-api.conf
VIRTUAL_ENV=/opt/virtenv
DEFAULT_TEST_RUNS_BASE_DIR=/var/test-runs

# --- Dates according to ISO8601, "JJJJ-MM-DD ..."
COMMITBEFORE="2025-09-08 14:45:51 +0200"
## --- If $CLONEBASIL == 1, perform a fresh clone.
CLONEBASIL=-1
## --- get current version (HEAD) $GITGOBACK == 0 or go back in time > 0
## --- $GITGOBACK < 0: take specified time $COMMITBEFORE to determine the value of $GITGOBACK
GITGOBACK=11
# --- Dates according to ISO8601, "JJJJ-MM-DD ..."
COMMITBEFORE="2025-08-31 14:45:51 +0200"

### ####################################    main    ################################################
## --- constants:
REFERENCEDATE01="2025-08-31 14:45:51 +0200"  # Still with sqlite-database
## --- local functions -----------------------------------------------------------------------------
rcpdir() {
    local source_dir="$1"
    local dest_dir="$2"
    ## --- remove trailing slashes
    source_dir="${source_dir%/}"
    dest_dir="${dest_dir%/}"
    ## --- Rsync with error treatment
    if ! rsync -avq --partial --timeout=30 \
         "$source_dir"/ "$dest_dir"/ 2>/tmp/rsync_error; then
        echo "Error: rsync operation failed"
        echo "Error details:"
        cat /tmp/rsync_error
        rm -f /tmp/rsync_error
        return 1
        exit 1;
    fi
    echo "Rsync completed successfully"$'\n'
    rm -f /tmp/rsync_error
    return 0
}
### --- main -------------------------------------------------------------------
clear
# --- check if rsync is available
if ! command -v rsync &> /dev/null; then
        echo "Error: rsync is not installed, Execution terminates!"$'\n'; exit 1;
fi
echo ===================================================================
echo install BASIL-API:
echo -------------------------------------------------------------------
cd ~
echo $(pwd)

# --- check if BASIL repository should be cloned ---------------------------------------------------
if [ $CLONEBASIL -eq 0 ]; then
  # rm -R $BASIL_BUILD_DIR
    if ! [ -d $BASIL_BUILD_DIR ]; then
        echo "---  BASIL repository not found! Repository will be cloned!  ---"
        git clone $BASIL_REPOSITORY $BASIL_BUILD_DIR
    else
        echo "---  Keep current version of BASIL.  --------------------------------------------"$'\n'
    fi
else
    echo $'\n'"--- re-clone BASIL git repository. -----------------------------------"
    if [ -d $BASIL_BUILD_DIR ]; then
        echo ---  re-establish folder $BASIL_BUILD_DIR    -------------------
        rm -R $BASIL_BUILD_DIR
    fi
    mkdir -p $BASIL_BUILD_DIR
    ## --- clone git repository --------------------------------------------
    git clone $BASIL_REPOSITORY $BASIL_BUILD_DIR
    echo $'\n'"=== END git clone =============================================================="$'\n'
fi

# --- Decide which mode to find the correct commit of BASIL go back in time or in commits / HEADS
cd "$BASIL_BUILD_DIR" || { echo "Error: Folder $BASIL_BUILD_DIR not found!"; exit 1; }
if [ $GITGOBACK -lt 0 ]; then
    # --- validate correct time format of $COMMITBEFORE
    if [[ ! "$COMMITBEFORE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}\ [+-][0-9]{4}$ ]]; then
        echo "Error: Invalid date format: $COMMITBEFORE"$'\n'; exit 1;
    fi
    # --- Check if latest commit date is after time: $COMMITBEFORE
    latest_commit_date=$(git log -1 --format=%cd --date=format:%s)
    commit_before_date=$(date -d "$COMMITBEFORE" +%s 2>/dev/null)
    if [ "$commit_before_date" -gt "$latest_commit_date" ]; then
        echo "Warning: Date $COMMITBEFORE is after the latest commit"
        echo "This will return the latest commit (HEAD)"
        # Optional: exit 1 falls gewünscht
    fi
    echo "--- Go back to commit that lies before:  $COMMITBEFORE  ---"
    # --- get the latest commit that is strictly before the reference date
    ref_commit=$(git rev-list -1 --before="$COMMITBEFORE" HEAD)
    if [ -z "$ref_commit" ]; then
        echo "No commit found before $COMMITBEFORE"
        exit 1
    fi
    # --- set $GITGOBACK correctly to catch last commit that lies before $COMMITBEFORE
    GITGOBACK=$(git rev-list --count "$ref_commit"..HEAD)
fi
# ---
TOTALNUMBEROFCOMMITS=$(git rev-list --count HEAD)
if [ $GITGOBACK -gt $TOTALNUMBEROFCOMMITS ]; then
    echo $'\n'" ----  GITGOBACK = $GITGOBACK too high, maximum is $TOTALNUMBEROFCOMMITS  ----"$'\n'
    echo $'\n'"=========================================================================="$'\n'
    exit 1;
fi
# --- Check if it is a "merge commit" --------------------------------------------------------------
if ! git revert --no-commit HEAD~$GITGOBACK..HEAD 2>/dev/null; then
    echo $'\n'"=========================================================================="$'\n'
    echo "---   Error: git revert failed likely due to merge commits or other issues."
    echo "---   Specify another commit! --- Maybe Refresh local copy of repository. "
    echo "---   Specified or determined GITGOBACK is $GITGOBACK. --- Execution terminates now! ---"
    echo $'\n'"=========================================================================="$'\n'
fi
# --- open with specified or determined HEAD=$GITGOBACK --------------------------------------------
# echo "TOTALNUMBEROFCOMMITS:  $TOTALNUMBEROFCOMMITS"$'\n'
COMMITDATE=$(git show -s --format=%ci HEAD~$GITGOBACK)
## --- Get the original commit message (subject + body)
ORIGMSG=$(git show -s --format=%B HEAD~$GITGOBACK)
## --- Extract commit number if present, don’t exit if missing
COMMITNUMBER=$(grep -oP '#\K[0-9]+' <<<"$ORIGMSG" || true)
## --- Combine them into one commit message (quote properly!)
COMMITMESSAGE="Revert of commit HEAD~${GITGOBACK} from: ${COMMITDATE}"
echo "---  Commit message:  -------------------------------------------------------------"$'\n'
echo ${ORIGMSG}
echo $'\n'"------------------------------------------------------------------------------"$'\n'

# echo "DBG --- This is line $LINENO, next: git commit -m "
## --- revert and commit, if $GITGOBACK is greater then 0: -----------------------------------------
if [ $GITGOBACK -gt 0 ]; then
    echo " ---  GITGOBACK = $GITGOBACK is greater then 0:  --- "
    # --- Following commands should not stop the script execution, true = Exit-Code 0
    git revert --no-commit HEAD~$GITGOBACK..HEAD 2>/dev/null || true
    git commit -m "$COMMITMESSAGE"  2>/dev/null || true
fi
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
if [[ -v $TEST_RUNS_BASE_DIR ]]; then
    chown -R www-data:www-data $BASIL_API && chmod -R 755 $TEST_RUNS_BASE_DIR
else
	chown -R www-data:www-data $BASIL_API && chmod -R 755 $DEFAULT_TEST_RUNS_BASE_DIR
fi

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
os.environ['BASIL_DB_PASSWORD'] = 'rm_Zero' \n\
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
## --- Install Flask inside the virtual environment
$VIRTUAL_ENV/bin/pip install --no-cache-dir -r $BASIL_API/requirements.txt
## --- configure folder structure:
echo --- configure folder structure:
chown -R www-data:www-data $BASIL_API/api/ssh_keys
chmod -R 750 $BASIL_API/api/ssh_keys
mkdir -p /var/test-runs
chmod -R 750 /var/test-runs
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
printf "<VirtualHost *:5000> \n\
    ServerName $SERVER_NAME \n\
    ServerAlias $SERVER_ALIAS \n\
    ServerAdmin $SERVER_ADMIN \n\
    # --- WSGI - stuff:
    WSGIProcessGroup basil-api \n\
    WSGIDaemonProcess basil-api python-home=$VIRTUAL_ENV python-path=$BASIL_API user=www-data group=www-data threads=5 \n\
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
## --- activate BASIL-API apache2-config file and restart apache2 server
echo --- send Apache2 to FOREGROUND: apache2ctl -D FOREGROUND ----------
apache2ctl -D FOREGROUND
echo --- activate BASIL-API apache2-config file
sudo a2ensite basil-api.conf
echo --- restart apache2 via command: sudo apachectl graceful ---------------------------------$'\n'
sudo apachectl graceful
echo --- end main --- rights of folder: $BASIL_API  -------------------------------------------$'\n'
ls -ld $BASIL_API/
echo ---  $WSGI_SCRIPT  -----------------------------------------------------------------------$'\n'
cat $WSGI_SCRIPT
echo $'\n'--- run gunicorn: -------------------------------------------------------------------$'\n'
cd $BASIL_API/api
/opt/virtenv/bin/gunicorn --bind 0.0.0.0:5000 api:app
cd ~
echo --- END ----------------------------------------------------------------------------------$'\n'
