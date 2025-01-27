#/bin/sh

# Example BASIL deployment script

api_server_url=http://localhost
api_distro=fedora
api_port=5000
app_port=9000
admin_pw=1234

OPTSTRING=":b:d:f:p:u:h"

usage()
{
    cat <<-EOF >&2

        BASIL Deployment script

        usage: ${0##*/} [ -b API_PORT ] [ -u URL ] [ -f APP_PORT ] [ -p ADMIN_PASSWRORD ]
        
        -b API_PORT         Api (backend) port
        -d API_DISTRO       Distro used to deploy the api 'fedora' or 'debian', default is 'fedora'
                            That will be also the default distro used in BASIL test infrastructure when
                            user select Container as target test environment
        -f APP_PORT         App (frontend) port                        
        -p ADMIN_PASSWRORD  Admin user default password (username: admin)
                            use single quote around your password
        -u URL              Full base url
                            - http://localhost if you want to evaluate it on your machine
                            - http://<ip address> if you want to use a centralized machine 
                            in the local network (e.g.: http://192.168.1.15)
        
        example: ${0##*/} -b 5005 -u 'http://192.168.1.15' -f 9005 -p '!myStrongPasswordForAdmin!'

        BASIL (frontend) will be available at [URL][APP_PORT] e.g. http://192.168.1.15:9005
        BASIL Api (backend) will be available at [URL][API_PORT] e.g. http://192.168.1.15:5005
        To test the Api you can check the /version endpoint e.g. http://192.168.1.15:5005/version

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
      fi
      ;;
    f)
      app_port=${OPTARG}
      ;;
    p)
      admin_pw=${OPTARG}
      ;;
    u)
      api_server_url=${OPTARG}
      ;;
    h)
      usage
  esac
done

echo -e "\n###################################################################"
echo -e "### prepairing BASIL deployment "
echo -e "### kill all running podman container\n"

podman stop --all

echo -e "\n### api_server_url = ${api_server_url}"
echo -e "### api distro = ${api_distro}"
echo -e "### api port = ${api_port}"
echo -e "### app port = ${app_port}"
echo -e "### admin pw = ${admin_pw}"

echo -e "\n###################################################################"
echo -e "### building api container\n"

api_containerfile=Containerfile-api-fedora
if [ ${api_distro} == "debian" ]; then
  api_containerfile=Containerfile-api-debian
fi

podman build \
  --build-arg="ADMIN_PASSWORD=${admin_pw}" \
  --build-arg="API_PORT=${api_port}" \
  -f ${api_containerfile} \
  -t basil-api-image .

echo -e "\n###################################################################"
echo -e "### building app container\n"

podman build \
  --build-arg="API_ENDPOINT=${api_server_url}:${api_port}" \
  --build-arg="APP_PORT=${app_port}" \
  -f Containerfile-app \
  -t basil-app-image .

echo -e "\n###################################################################"
echo -e "### create and mount volumes\n"

list='basil-db-vol basil-ssh-keys-vol basil-tmt-logs-vol'
for element in $list;
do
    podman volume exists "${element}"   # check if volume already exists
    if [ $? == 0 ]; then
       echo "volume "${element}" already exists"
    else
       echo "volume $element does not exist"
       podman volume create "${element}"
    fi
    podman volume mount "${element}"
done

echo -e "\n###################################################################"
echo -e "### install cronjobs\n"

cp -a misc/cronjobs/daily/. /etc/cron.daily/

echo -e "\n###################################################################"
echo -e "### start api container\n"

podman run \
   -d \
   --privileged \
   --network=host \
   -v "basil-db-vol:/BASIL-API/db/sqlite3" \
   -v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
   -v "basil-tmt-logs-vol:/var/tmp/tmt" \
   basil-api-image

echo -e "\n###################################################################"
echo -e "### start app container\n"

podman run \
   -d \
   --network=host \
   basil-app-image

echo -e "\n###################################################################"
echo -e "### list running containers\n"

podman ps

echo -e "\n###################################################################"
echo -e "### start now BASIL via chrome browser: ${api_server_url}:${app_port}\n"
