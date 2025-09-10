#!/bin/bash

# Example BASIL deployment script

api_server_url=http://localhost
api_distro=fedora
api_containerfile=Containerfile-api-fedora
api_port=5000
app_port=9000
admin_pw=1234
db_name=basil
db_port=5432
db_password=default_db_password
testing=0

OPTSTRING=":b:d:e:f:p:t:u:w:h"
TITLE_COLOR_STR="\033[0;92;40m"
BODY_COLOR_STR="\033[0;97;40m"
ALERT_COLOR_STR="\033[0;31;40m"
RESET_COLORS_STR="\033[0m"
BASIL_NETWORK="basil-network"
BASIL_POD="basil-pod"
TAG=$(git describe --tags 2>/dev/null | sed 's/-/_/g')
TAG=${TAG:-"latest"}

# ---------------------------------------
# Functions
# ---------------------------------------
sanitize_git_tag_for_container_name()
{
  local raw_tag="$1"

  # Convert to lowercase using `tr`
  local tag=$(echo "$raw_tag" | tr '[:upper:]' '[:lower:]')

  # Replace all characters that are not a-z, 0-9, ., _, or - with dashes
  tag=$(echo "$tag" | sed 's/[^a-z0-9_.-]/-/g')

  # Remove leading/trailing dashes (optional cleanup)
  tag="${tag##[-]}"
  tag="${tag%%[-]}"

  # Ensure it starts with a letter (prepend 'tag-' if needed)
  if [[ ! "$tag" =~ ^[a-z] ]]; then
    tag="tag-$tag"
  fi

  echo "$tag"
}


remove_container()
{
  local container_name=$1
  if podman container exists $container_name; then
    echo "Container $container_name exists, removing it"
    podman rm -f $container_name
  fi
}

echoSectionTitle()
{
    local title=$1
    echo -e "\n${TITLE_COLOR_STR}"
    echo -e "###################################################################"
    echo -e "###                 ${title}"
    echo -e "###################################################################"
}

usage()
{
    cat <<-EOF >&2

        BASIL Deployment script

        usage: ${0##*/} [ -b API_PORT ] [ -u URL ] [ -f APP_PORT ] [ -p ADMIN_PASSWRORD ]
        -b API_PORT         Api (backend) port
        -d API_DISTRO       Distro used to deploy the api 'fedora' or 'debian', default is 'fedora'
                            That will be also the default distro used in BASIL test infrastructure when
                            user select Container as target test environment
        -e ENV_FILE         Filepath of an environment file you want to inject into the API Container
        -f APP_PORT         App (frontend) port
        -p ADMIN_PASSWRORD  Admin user password (username: admin) - Only if testing is off
                            use single quote around your password
        -t TESTING          1 to enable Testing
        -u URL              Full base url
                            - http://localhost if you want to evaluate it on your machine
                            - http://<ip address> if you want to use a centralized machine
                            in the local network (e.g.: http://192.168.1.15)
        -w DB_PASSWPRD      password of the basil-admin user of the postgreSQL database

        example: ${0##*/} -b 5005 -u 'http://192.168.1.15' -f 9005 -p '!myStrongPasswordForAdmin!' -w 'dbSecret123'
        example for testing: ${0##*/} -t 1 -b 5005 -u 'http://192.168.1.15' -f 9005 -p '!myStrongPasswordForAdmin!' -w 'dbSecret123'

        BASIL (frontend) will be available at [URL][APP_PORT] e.g. http://192.168.1.15:9005
        BASIL Api (backend) will be available at [URL][API_PORT] e.g. http://192.168.1.15:5005
         - To test the Api you can check the /version endpoint e.g. http://192.168.1.15:5005/version
        BASIL DB will be available at [URL][DB_PORT] e.g. http://192.168.1.15:5432

	EOF
exit 0
}

while getopts ${OPTSTRING} opt; do
    case ${opt} in
        b)
        api_port=${OPTARG}
        ;;
        d)
        if [ ${OPTARG} == "debian" ]; then
            api_distro=debian
            api_containerfile=Containerfile-api-debian
        fi
        ;;
        e)
        environment_file=${OPTARG}
        ;;
        f)
        app_port=${OPTARG}
        ;;
        p)
        admin_pw=${OPTARG}
        ;;
        t)
        testing=${OPTARG}
        ;;
        u)
        api_server_url=${OPTARG}
        ;;
        w)
        db_password=${OPTARG}
        ;;
        h)
        usage
        ;;
    esac
done

SANITIZED_TAG_FOR_CONTAINER_NAME=$(sanitize_git_tag_for_container_name ${TAG})
BASIL_API_CONTAINER=basil-api-${SANITIZED_TAG_FOR_CONTAINER_NAME}
BASIL_APP_CONTAINER=basil-app-${SANITIZED_TAG_FOR_CONTAINER_NAME}
BASIL_DB_CONTAINER=basil-db-${SANITIZED_TAG_FOR_CONTAINER_NAME}

if [ "$testing" -eq 1 ]; then
  db_name=test
  admin_pw=dummy_password
fi

# ---------------------------------------
echo -e "\n${TITLE_COLOR_STR}"
clear


# ---------------------------------------
echoSectionTitle "Prepairing BASIL deployment"

echo -e "${TITLE_COLOR_STR}\n> kill all running podman container\n${BODY_COLOR_STR}"
podman stop --all

echo -e "${TITLE_COLOR_STR}\n> Parameters\n${BODY_COLOR_STR}"
echo -e " - api_server_url = ${api_server_url}"
echo -e " - api distro = ${api_distro}"
echo -e " - api port = ${api_port}"
echo -e " - app port = ${app_port}"
echo -e " - admin pw = ${admin_pw}"
echo -e " - environment file = ${environment_file:=''}"
echo -e " - tag = ${TAG}"
echo -e " - db name = ${db_name}"
echo -e " - db port = ${db_port}"
echo -e " - db password = ${db_password}"
echo -e " - testing = ${testing}"


# ---------------------------------------
echoSectionTitle "Remove existing containers"

remove_container $BASIL_API_CONTAINER
remove_container $BASIL_APP_CONTAINER
remove_container $BASIL_DB_CONTAINER


# ---------------------------------------
echoSectionTitle "Create podman pod"

# Check if the pod already exists
if podman pod exists "$BASIL_POD"; then
  echo "Pod $BASIL_POD exists. Removing..."
  podman pod rm -f "$BASIL_POD"
else
  echo "Pod $BASIL_POD does not exist."
fi

# Check if network already exists
if podman network exists "$BASIL_NETWORK"; then
  echo "Network $BASIL_NETWORK exists. Removing..."
  podman network rm "$BASIL_NETWORK"
else
  echo "Network $BASIL_NETWORK does not exist."
fi

podman network create ${BASIL_NETWORK}

podman pod create \
  --name ${BASIL_POD} \
  --network ${BASIL_NETWORK} \
  --publish ${db_port}:${db_port} \
  --publish ${api_port}:${api_port} \
  --publish ${app_port}:${app_port}


# ---------------------------------------
echoSectionTitle "Building API container"

podman build \
    --build-arg="ADMIN_PASSWORD=${admin_pw}" \
    --build-arg="API_PORT=${api_port}" \
    --build-arg="DB_PORT=${db_port}" \
    --build-arg="TESTING=${testing}" \
    --build-arg="DB_PASSWORD=${db_password}" \
    -f ${api_containerfile} \
    -t basil-api-image:${TAG} .


# ---------------------------------------
echoSectionTitle "Building APP container"

echo -e "\n${BODY_COLOR_STR}"
podman build \
    --build-arg="API_ENDPOINT=${api_server_url}:${api_port}" \
    --build-arg="APP_PORT=${app_port}" \
    -f Containerfile-app \
    -t basil-app-image:${TAG} .


# ---------------------------------------
echoSectionTitle "Create and mount volumes"

echo -e "\n${BODY_COLOR_STR}"
list='basil-configs-vol basil-db-vol basil-ssh-keys-vol basil-tmt-logs-vol basil-user-files-vol'
for element in $list;
do
    podman volume exists "${element}"  # check if volume already exists
    if [ $? == 0 ]; then
        echo "volume "${element}" already exists"
        if [ "${element}" == "basil-db-vol" ]; then
            echo -e "${ALERT_COLOR_STR}API container will use existing db volume ${element}."
            echo -e "The admin password is the one in the existing volume ${element}."
            echo -e "To set and use the password '${admin_pw}', please delete/rename the existing volume ${element}."
            echo -e "\n${BODY_COLOR_STR}"
        fi
    else
        echo "volume $element does not exist"
        podman volume create "${element}"
    fi
    podman volume mount "${element}" || true
done


# ---------------------------------------
echoSectionTitle "Install cronjobs"

echo -e "\n${BODY_COLOR_STR}"
sudo cp -va misc/cronjobs/daily/. /etc/cron.daily/ || echo "WARNING: Unable to install cronjobs"


# ---------------------------------------
echoSectionTitle "Start PostgreSQL DB container"

echo -e "\n${BODY_COLOR_STR}"
podman run \
  --detach \
  --name ${BASIL_DB_CONTAINER} \
  --pod ${BASIL_POD} \
  -e POSTGRES_USER=basil-admin \
  -e POSTGRES_PASSWORD=${db_password} \
  -e POSTGRES_DB=${db_name} \
  -v basil-db-vol:/var/lib/postgresql/data \
  docker.io/library/postgres:15

# wait until the db container is up
for i in {1..10}; do
  if podman exec ${BASIL_DB_CONTAINER} pg_isready -U postgres; then
    echo "PostgreSQL container ${BASIL_DB_CONTAINER} is ready"
    break
  fi
  echo "Waiting for PostgreSQL container ${BASIL_DB_CONTAINER} to be ready..."
  sleep 10
done

# ---------------------------------------
echoSectionTitle "Start API container"

echo -e "\n${BODY_COLOR_STR}"

podman_cmd="podman run"
if [ -n "$environment_file" ] && [ -f "$environment_file" ]; then
  echo -e "\nAdding environment file $environment_file"
  podman_cmd="$podman_cmd --env-file $environment_file"
fi

podman_cmd="$podman_cmd --name ${BASIL_API_CONTAINER}"
podman_cmd="$podman_cmd --detach --privileged --pod=${BASIL_POD}"
podman_cmd="$podman_cmd -v basil-configs-vol:/BASIL-API/api/configs"
podman_cmd="$podman_cmd -v basil-ssh-keys-vol:/BASIL-API/api/ssh_keys"
podman_cmd="$podman_cmd -v basil-user-files-vol:/BASIL-API/api/user-files"
podman_cmd="$podman_cmd -v basil-tmt-logs-vol:/var/tmp/tmt"
podman_cmd="$podman_cmd basil-api-image:${TAG}"

$podman_cmd


# ---------------------------------------
echoSectionTitle "Start APP container"

echo -e "\n${BODY_COLOR_STR}"
podman run \
    --name ${BASIL_APP_CONTAINER} \
    --detach \
    --pod=${BASIL_POD} \
    basil-app-image:${TAG}


# ---------------------------------------
echoSectionTitle "List running containers"

echo -e "\n${BODY_COLOR_STR}"
podman ps

echo -e "\n${TITLE_COLOR_STR}"
echo -e "###################################################################"
echo -e "### BASIL in now available in your browser at: ${ALERT_COLOR_STR}${api_server_url}:${app_port}"
echo -e "${TITLE_COLOR_STR}###################################################################"
echo -e "${RESET_COLORS_STR}"
