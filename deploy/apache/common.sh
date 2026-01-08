#! /bin/bash -e

source .env

## --- If $CLONEBASIL == 1, perform a fresh clone.
CLONEBASIL=${BASIL_GITCLONE:-1}
## --- get current version (HEAD) $GITGOBACK == 0 or go back in time > 0
## --- $GITGOBACK < 0: take specified time $COMMITBEFORE to determine the value of $GITGOBACK
GITGOBACK=${BASIL_GITGOBACK:-0}
# --- Dates according to ISO8601, "JJJJ-MM-DD ..."
TOMORROWDATE=$(date -d 'tomorrow 08:00' '+%Y-%m-%d %H:%M:%S %z')
COMMITBEFORE="${BASIL_COMMITBEFORE:-$TOMORROWDATE}"

## --- Functions ---------------------------------------------------------------------------------------
clone_basil_repo_if_needed() {
    local _BASIL_REPOSITORY="${1}"
    local _BASIL_BUILD_DIR="${2}"
    local _CLONEBASIL=${3//[^0-9-]/}
    local _GITGOBACK=${4//[^0-9-]/}
    local _COMMITBEFORE="${5}"
    echo "DBG: --- Function: clone_basil_repo_if_needed() --- \$_CLONEBASIL:  ${_CLONEBASIL} ----"
    # --- check if BASIL repository should be cloned ---------------------------------------------------
    if (( _CLONEBASIL = 0 )); then
        echo "DBG: --- Function: clone_basil_repo_if_needed()  if [ $_CLONEBASIL -eq 0 ]; then ----"
        # rm -R $_BASIL_BUILD_DIR
        if ! [ -d $_BASIL_BUILD_DIR ]; then
            echo "---  BASIL repository not found! Repository will be cloned!  ---"
            git clone $_BASIL_REPOSITORY $_BASIL_BUILD_DIR
        else
            echo "---  Keep current version of BASIL.  --------------------------------------------"$'\n'
        fi
    else
        echo $'\n'"--- re-clone BASIL git repository. -----------------------------------"
        if [ -d $_BASIL_BUILD_DIR ]; then
            echo ---  re-establish folder $_BASIL_BUILD_DIR    -------------------
            rm -R $_BASIL_BUILD_DIR
        fi
        mkdir -p $_BASIL_BUILD_DIR
        ## --- clone git repository --------------------------------------------
        git clone $_BASIL_REPOSITORY $_BASIL_BUILD_DIR
        echo $'\n'"--- END git clone -------------------------------------------------------------"$'\n'
    fi


    # --- Decide which mode to find the correct commit of BASIL go back in time or in commits / HEADS
    echo "--- change directory to: ${_BASIL_BUILD_DIR} --------------------------------------------"
    printf 'DBG: $_GITGOBACK <%q>\n' "${_GITGOBACK}" # check if non-pritable chars (\r \n) exist
    cd "${_BASIL_BUILD_DIR}" || { echo "Error: Folder $_BASIL_BUILD_DIR not found!"; exit 1; }
    if (( _GITGOBACK < 0 )); then
        # --- validate correct time format of $_COMMITBEFORE
        if [[ ! "$_COMMITBEFORE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}\ [0-9]{2}:[0-9]{2}:[0-9]{2}\ [+-][0-9]{4}$ ]]; then
            echo "Error: Invalid date format: $_COMMITBEFORE"$'\n'; exit 1;
        fi
        # --- Check if latest commit date is after time: $_COMMITBEFORE
        latest_commit_date=$(git log -1 --format=%cd --date=format:%s)
        commit_before_date=$(date -d "$_COMMITBEFORE" +%s 2>/dev/null)
        if [ "$commit_before_date" -gt "$latest_commit_date" ]; then
            echo "Warning: Date $_COMMITBEFORE is after the latest commit"
            echo "This will return the latest commit (HEAD)"
            # Optional: exit 1 falls gewünscht
        fi
        echo "--- Go back to commit that lies before:  $_COMMITBEFORE  ---"
        # --- get the latest commit that is strictly before the reference date
        ref_commit=$(git rev-list -1 --before="$_COMMITBEFORE" HEAD)
        if [ -z "$ref_commit" ]; then
            echo "No commit found before $_COMMITBEFORE"
            exit 1
        fi
        # --- set $_GITGOBACK correctly to catch last commit that lies before $_COMMITBEFORE
        _GITGOBACK=$(git rev-list --count "$ref_commit"..HEAD)
    fi
    # ---

    TOTALNUMBEROFCOMMITS=$(git rev-list --count HEAD)
    if (( _GITGOBACK > TOTALNUMBEROFCOMMITS )); then
        echo $'\n'" ----  _GITGOBACK = $_GITGOBACK too high, maximum is $TOTALNUMBEROFCOMMITS  ----"$'\n'
        echo $'\n'"=========================================================================="$'\n'
        exit 1;
    fi

    # --- Check if it is a "merge commit" --------------------------------------------------------------
    if ! git revert --no-commit HEAD~$_GITGOBACK..HEAD 2>/dev/null; then
        echo $'\n'"=========================================================================="$'\n'
        echo "---   Error: git revert failed likely due to merge commits or other issues."
        echo "---   Specify another commit! --- Maybe Refresh local copy of repository. "
        echo "---   Specified or determined _GITGOBACK is $_GITGOBACK. --- Execution terminates now! ---"
        echo $'\n'"=========================================================================="$'\n'
    fi

    # --- open with specified or determined HEAD=$_GITGOBACK --------------------------------------------
    # echo "TOTALNUMBEROFCOMMITS:  $TOTALNUMBEROFCOMMITS"$'\n'
    COMMITDATE=$(git show -s --format=%ci HEAD~$_GITGOBACK)
    ## --- Get the original commit message (subject + body)
    ORIGMSG=$(git show -s --format=%B HEAD~$_GITGOBACK)
    ## --- Extract commit number if present, don’t exit if missing
    COMMITNUMBER=$(grep -oP '#\K[0-9]+' <<<"$ORIGMSG" || true)
    ## --- Combine them into one commit message (quote properly!)
    COMMITMESSAGE="Revert of commit HEAD~${_GITGOBACK} from: ${COMMITDATE}"
    echo "---  Commit message:  -------------------------------------------------------------"$'\n'
    echo Commit Date: ${COMMITDATE}
    echo ${ORIGMSG}
    echo $'\n'"------------------------------------------------------------------------------"$'\n'
    # echo "DBG --- This is line $LINENO, next: git commit -m "

    ## --- revert and commit, if $_GITGOBACK is greater then 0: -----------------------------------------
    if (( _GITGOBACK > 0 )); then
        echo " ---  _GITGOBACK = $_GITGOBACK is greater then 0:  --- "
        # --- Following commands should not stop the script execution, true = Exit-Code 0
        git revert --no-commit HEAD~$_GITGOBACK..HEAD 2>/dev/null || true
        git commit -m "$COMMITMESSAGE"  2>/dev/null || true
    fi
    #---
    echo $'\n'"=== END function <clone_basil_repo_if_needed>  ===================================="$'\n'
    return 0
}


install_package() {
  PACKAGE=$1
  if ! dpkg -s "$PACKAGE" &> /dev/null; then
    echo
    echo "---> Installing $PACKAGE..."
    sudo apt install -y "$PACKAGE"
  else
    echo
    echo "---> $PACKAGE is already installed."
  fi
}

add_port_to_listen() {
    local file_path=$(echo "$1" | tr -cd '[:print:]')     # Parameter A: file path
    local search_string=$(echo "$2" | tr -cd '[:print:]') # Parameter B: string

    # Validate parameters
    if [[ -z "$file_path" || -z "$search_string" ]]; then
        echo "Usage: add_port_to_listen <file-path> <string>" >&2
        return 1
    fi

    if [[ ! -f "$file_path" ]]; then
        echo "Error: File not found: $file_path" >&2
        return 1
    fi

    #: Check if Listen <port> already exists (any whitespace)
    if grep -Eq "^[[:space:]]*Listen[[:space:]]+$search_string([[:space:]]*|$)" "$file_path"; then
        echo "Listen $search_string already present"
        return 0
    else
        #: Append safely
        # echo "Listen $search_string" >> "$file_path"
        echo "Listen ${search_string}" | sudo tee -a "$file_path" > /dev/null
        echo "Added: Listen $search_string"
    fi
    echo "---------------------------------------------------------------------------------"
    echo "****  END add_port_to_listen                                                 ****"
    echo "---------------------------------------------------------------------------------"
    return 0
}


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


