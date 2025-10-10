#! /bin/bash -e
## ### this script has to be run under admin previleges!!! #########################################
## --- open toot CLI, command (or similar): su -
## #################################################################################################
## Version: 1.0  
## Initial Author: Stefan Pofahl (with the support of AI and Luigi pellecchialuigi)
## #################################################################################################

### --- individual configuration variables: ---------------------------------------------------------
SERVER_NAME=Your.Host.IP.Num
SERVER_ALIAS=hostname.domain.local
SERVER_ADMIN=admin.name@domaine.local
## ---
BASIL_REPOSITORY=https://github.com/elisa-tech/BASIL.git
BASIL_BUILD_DIR=/tmp/basil
BASIL_BUILD_APP=$BASIL_BUILD_DIR/app
BASIL_FRONT_END=/var/www/basil
BASIL_FRONT_END_CONF=/etc/apache2/sites-available/basil.conf
BASIL_API=/var/www/basil-api
API_ENDPOINT=http://$SERVER_NAME:5000
APPCONSTANTS_FILE=$BASIL_BUILD_APP/src/app/Constants/constants.tsx

### --- general instructions (0 == FALSE, > 0 TRUE ):-----------------------------------------------
## --- install mandatory software / toolchain:
SETUPTOOLCHAIN=1
UPDATENODEPACKAGES=1
## --- If $CLONEBASIL == 1, perform a fresh clone.
CLONEBASIL=1
## --- get current version (HEAD) $GITGOBACK == 0 or go back in time > 0
## --- $GITGOBACK < 0: take specified time $COMMITBEFORE to determine the value of $GITGOBACK
GITGOBACK=0
# --- Dates according to ISO8601, "JJJJ-MM-DD ..."
COMMITBEFORE="2025-08-31 14:45:51 +0200"

### ####################################    main    ################################################
## --- constants:
REFERENCEDATE01="2025-08-31 14:45:51 +0200"  # Still with sqlite-database
## ---
clear
echo ===============================================================================================
echo                      install BASIL-FRONT-END:
echo ===============================================================================================$'\n'
if [ $SETUPTOOLCHAIN -gt 0 ]; then
	echo ===============================================================================================
	echo                      install necessary packages / tools:
	echo ===============================================================================================$'\n'
	apt update
	apt install -y curl gnupg
	apt install -y python3 python3-pip python3-venv libapache2-mod-wsgi-py3
	## --- run auto remove (delete old packages that are not needed) ---
	apt autoremove && apt clean
    rm -rf /var/lib/apt/lists/*
	## --- enable packages and restart apache2:
	a2enmod wsgi
	systemctl restart apache2
	echo ===   END   of install necessary packages / tools   ===========================================$'\n'
	## --- delete previous / current node.js-installation, if it exist:
	if [ -d $$HOME/.nvm ]; then
		rm -R $HOME/.nvm
	fi
fi
# --- check if npm is installed: -------------------------------------------------------------------
if ! command -v npm >/dev/null 2>&1 ;  then
	echo $'\n'"************************************************************************************************"
	echo "***    Install nvm v10.X.Y and node.js v22.X.Y             *************************************"
	echo "***    please refer to: https://nodejs.org/en/download     *************************************"
	echo "************************************************************************************************"$'\n'
    # --- be shure old nvm is deleted, before download!
   	if [ -d $$HOME/.nvm ]; then
		rm -R $HOME/.nvm
	fi
	echo ---- down load nvm: ---------------------------------------------------------------------$'\n'
	curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
	echo ---- install nvm inside the root HOME folder: -------------------------------------------$'\n'
    export NVM_DIR="$HOME/.nvm"
	[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
	[ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
	nvm install --lts
	UPDATENODEPACKAGES=1
fi
echo "***   Version of npm and node.js: *********************************************************"
echo "      - javascript package manager, npm: v"$(npm -v)
echo "      - node.js:                         "$(node -v)
echo "-------------------------------------------------------------------------------------------"
echo "   Please check the the messages displayed during script execution. Things may change ..."
echo "   if you see nvm related massages you may try the option UPDATENODEPACKAGES=1 (see above)"
echo "-------------------------------------------------------------------------------------------"

if [ $UPDATENODEPACKAGES -gt 0 ]; then
	## --- some nmp stuff:
	echo "***   Repair and update node.js packages:      ********************************************"
	npm i --package-lock-only
	npm audit fix
	npx update-browserslist-db@latest
	npm update chokidar
	npm update --save
fi
#echo "This is line $LINENO"
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
    exit 1
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

## --- revert and commit, if $GITGOBACK is greater then 0: -----------------------------------------
if [ $GITGOBACK -gt 0 ]; then
    echo " ---  GITGOBACK = $GITGOBACK is greater then 0:  --- "
    # --- Following commands should not stop the script execution, true = Exit-Code 0
    git revert --no-commit HEAD~$GITGOBACK..HEAD 2>/dev/null || true
    git commit -m "$COMMITMESSAGE"  2>/dev/null || true
	echo $'\n'"=== Content of local copy of BASIL repository reverted to: COMMITDATE ============="$'\n'
fi

## --- Build front end --------------------------------------------------
mkdir -p $BASIL_FRONT_END/app
cd $BASIL_BUILD_APP
ls -l $BASIL_BUILD_APP
echo --- Build BASIL Frontend Application ------------------------------
echo $(pwd)
echo ---  npm install --------------------------------------------------
npm install
echo ---  fine tune constants ------------------------------------------
if [ -f "$APPCONSTANTS_FILE" ]; then
    echo ---  "$APPCONSTANTS_FILE exists." -----------------------------
    ## --- Check if the variable exists inside this configuration file:
	if ! grep -q "^export const API_BASE_URL" "$APPCONSTANTS_FILE"; then
		echo "❌ API_BASE_URL not found in $APPCONSTANTS_FILE ❌"
		kill -9 $$
	fi
	## --- extract current value:
	current_value=$(grep -E "^export const API_BASE_URL" "$APPCONSTANTS_FILE" \
		 | sed -E "s/^export const API_BASE_URL = '(.*)'.*/\1/")
	echo "***   Definition of API_BASE_URL: $current_value   ***********"
	line=$(grep "^export const API_BASE_URL" "$APPCONSTANTS_FILE")
	echo "***   Whole line:                                  ***********"
	echo "$line"
	echo "--------------------------------------------------------------"
	## --- Replace old value with new one: $API_ENDPOINT
	sed -i "s#http://localhost:5000#${API_ENDPOINT}#g" $APPCONSTANTS_FILE
    ## --- Display line after modification:
	echo "***   New value of API_BASE_URL: $API_ENDPOINT  "
	line=$(grep "^export const API_BASE_URL" "$APPCONSTANTS_FILE")
	echo "***   Whole line of new definition:                ***********"
	echo "$line"'\n'
    echo "***   End of modification of $APPCONSTANTS_FILE   *******"$'\n'
else
    echo ===============================================================
    echo ***  ❌ERROR no $APPCONSTANTS_FILE $'\n'
    echo ***  Source code has changed!
    echo ***  Please investigate changes inside the source code of BASIL.
    echo ***  ❌Script execution terminates
    echo ===============================================================$'\n'
	## --- Kill the process
    kill -9 $$
fi
echo "---  npm run build ------------------------------------------------"'\n'
npm run build
echo === install and build done ========================================
# --- (re-)establish BASIL front-end folder: ---------------------------
if [ -d $BASIL_FRONT_END ]; then
   echo re-establish folder $BASIL_FRONT_END
   rm -R $BASIL_FRONT_END
fi
mkdir -p $BASIL_FRONT_END
## --- copy artefacts / compiled BASIL-application files to BASIL root
cp -r $BASIL_BUILD_APP/dist/* $BASIL_FRONT_END
## --- rights and ownership for Apache2 user:
chown -R www-data:www-data $BASIL_FRONT_END
chmod -R 755 $BASIL_FRONT_END
## --- create Apache2 VirtualHost Configuration file for BASIL FrontEnd:
printf "<VirtualHost *:9000> \n\
    ServerName $SERVER_NAME \n\
    ServerAlias $SERVER_ALIAS \n\
    ServerAdmin $SERVER_ADMIN \n\
    # --- \n\
    DocumentRoot $BASIL_FRONT_END \n\
    # ---
    <Directory \"$BASIL_FRONT_END\"> \n\
        Options Indexes FollowSymLinks \n\
        AllowOverride None \n\
        Require all granted \n\
        # allows React Router to take over routing from index.html \n\
        RewriteEngine On \n\
        RewriteBase / \n\
        RewriteRule ^index\.html - [L] \n\
        RewriteCond %%{REQUEST_FILENAME} !-f \n\
        RewriteCond %%{REQUEST_FILENAME} !-d \n\
        RewriteCond %%{REQUEST_URI} !\.[a-zA-Z0-9]{2,5}$ \n\
        RewriteRule . /index.html [L] \n\
    </Directory> \n\
    # --- Logging ---
    ErrorLog \${APACHE_LOG_DIR}/error.log \n\
    CustomLog \${APACHE_LOG_DIR}/access.log combined \n\
</VirtualHost>" > $BASIL_FRONT_END_CONF
echo  --- Apache2 BASIL conf-file written to: $BASIL_FRONT_END_CONF ---
## --- activate BASIL-API apache2-config file and restart apache2 server
echo --- activate BASIL-API apache2-config file
sudo a2ensite basil.conf
echo --- restart apache2 via command: sudo apachectl graceful ----------
sudo apachectl graceful
## --- display some information at the end -----------------------------
echo --- show Apache2 ports configuration file: ------------------------$'\n'
cat /etc/apache2/ports.conf
## ---
if [ $GITGOBACK -gt 0 ]; then
	echo "--- repository reverted to previous HEAD, Commit date of current commit is: $COMMITDATE_CURRENT" $'\n'
	echo "$COMMITMESSAGE"
fi

echo $'\n'--- END -----------------------------------------------------------$'\n'
