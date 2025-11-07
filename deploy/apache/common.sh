#! /bin/bash -e

source .env

## --- If $CLONEBASIL == 1, perform a fresh clone.
CLONEBASIL="${BASIL_GITCLONE:-1}"
## --- get current version (HEAD) $GITGOBACK == 0 or go back in time > 0
## --- $GITGOBACK < 0: take specified time $COMMITBEFORE to determine the value of $GITGOBACK
GITGOBACK="${BASIL_GITGOBACK:-0}"
# --- Dates according to ISO8601, "JJJJ-MM-DD ..."
TOMORROWDATE=$(date -d 'tomorrow 08:00' '+%Y-%m-%d %H:%M:%S %z')
COMMITBEFORE="${BASIL_COMMITBEFORE:-$TOMORROWDATE}"

clone_basil_repo_if_needed() {
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
    ## --- Add port to apache configuration
    NEW_PORT="$1"
    APACHE_PORTS=/etc/apache2/ports.conf
    ## --- find "Listen XX" (XX = port number), I have tried several variants, this works fine
    if grep -vE '^[[:space:]]*#' "$APACHE_PORTS" | grep -Eq "^[[:space:]]*Listen\b[[:space:]]+$NEW_PORT\b"; then
    # if grep -Eq "^[[:space:]]*Listen[[:space:]]+$NEW_PORT([[:space:]]|$)" "$APACHE_PORTS"; then
	echo "'Listen ${NEW_PORT}' already present in $APACHE_PORTS"
    else
	echo "New Port ${NEW_PORT} not specified in '$APACHE_PORTS'!"
	echo "Listen ${NEW_PORT}" | sudo tee -a /etc/apache2/ports.conf
	echo "Added 'Listen ${NEW_PORT}' to '$APACHE_PORTS'"
    fi
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


