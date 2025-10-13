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
APP_PORT="${BASIL_APP_PORT:-9000}"

## --- constants -----------------------------------------------------------------------------------
BASIL_REPOSITORY=https://github.com/elisa-tech/BASIL.git
BASIL_BUILD_DIR=/tmp/basil
BASIL_BUILD_APP=$BASIL_BUILD_DIR/app
BASIL_FRONT_END=/var/www/basil
BASIL_FRONT_END_CONF=/etc/apache2/sites-available/basil.conf
BASIL_API=/var/www/basil-api
API_ENDPOINT=http://${SERVER_NAME}:${API_PORT}
APPCONSTANTS_FILE=$BASIL_BUILD_APP/src/app/Constants/constants.tsx

### --- general instructions (0 == FALSE, > 0 TRUE ):-----------------------------------------------
## --- install mandatory software / toolchain:
SETUPTOOLCHAIN=1
UPDATENODEPACKAGES=1

### ####################################    main    ################################################
echo
echo ===============================================================================================
echo BASIL Frontend web application
echo ===============================================================================================$'\n'
if [ $SETUPTOOLCHAIN -gt 0 ]; then
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
    
    echo ---- download nvm: ---------------------------------------------------------------------$'\n'
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash
    echo ---- install nvm inside the root HOME folder: -------------------------------------------$'\n'
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && . "$NVM_DIR/bash_completion"
    nvm install --lts
fi

echo "***   Version of npm and node.js: *********************************************************"
echo "      - javascript package manager, npm: v"$(npm -v)
echo "      - node.js:                         "$(node -v)
echo "-------------------------------------------------------------------------------------------"
echo "   Please check the the messages displayed during script execution. Things may change ..."
echo "   if you see nvm related massages you may try the option UPDATENODEPACKAGES=1 (see above)"
echo "-------------------------------------------------------------------------------------------"

## --- Clone BASIL repo if needed --------------------------------------------------
clone_basil_repo_if_needed
cd $BASIL_BUILD_APP

if [ $UPDATENODEPACKAGES -gt 0 ]; then
    ## --- some nmp stuff:
    echo "***   Repair and update node.js packages:      ********************************************"
    npm i --package-lock-only
    npm audit fix
    npx update-browserslist-db@latest
    npm update chokidar
    npm update --save
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

## --- copy artifacts / compiled BASIL-application files to BASIL root
cp -r $BASIL_BUILD_APP/dist/* $BASIL_FRONT_END

## --- rights and ownership for Apache2 user:
chown -R www-data:www-data $BASIL_FRONT_END
chmod -R 755 $BASIL_FRONT_END

## --- Add port to Listen
add_port_to_listen "${APP_PORT}"

## --- create Apache2 VirtualHost Configuration file for BASIL FrontEnd:
printf "<VirtualHost *:${APP_PORT}> \n\
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

echo --- enable mod rewrite
sudo a2enmod rewrite

echo --- restart apache2 via command: sudo apachectl graceful ----------
sudo systemctl restart apache2

## --- display some information at the end -----------------------------
echo --- show Apache2 ports configuration file: ------------------------$'\n'
cat /etc/apache2/ports.conf

# Testing APP
echo --- Testing APP -------------------------------------------------------------$'\n'
curl -s -w "%{http_code}" http://${SERVER_NAME}:${APP_PORT}/version | grep -q "200" && echo "Test APP: OK" || echo "Test APP: FAIL"

echo $'\n'--- END -----------------------------------------------------------$'\n'
