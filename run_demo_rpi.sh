#/bin/sh

# BASIL Deployment script for Raspberry Pi in a local network
# tested with 
#   raspberry pi 4 model B
#   Linux raspberrypi 6.6.51+rpt-rpi-v8 #1" 
#   SMP PREEMPT Debian 1:6.6.51-1+rpt3 (2024-10-08) aarch64 GNU/Linux"
#   Raspbian GNU/Linux 12

api_server_url=localhost
api_port=5000
app_port=9000
admin_pw=1234

OPTSTRING=":b:u:f:p:h"

usage()
{
    cat <<-EOF >&2

        BASIL Deployment script for Raspberry Pi in a local network

        usage: ${0##*/} [ -b API_PORT ] [ -u URL ] [ -f APP_PORT ] [ -p ADMIN_PASSWRORD ]
        
        -b API_PORT         Api (backend) port
        -f APP_PORT         App (frontend) port                        
        -p ADMIN_PASSWRORD  Admin user default password (username: admin)
                            use single quote around your password
        -u URL              Url, depending on the raspberry ip address in the local
                            network (e.g.: http://192.168.1.15)
        
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
    u)
      api_server_url=${OPTARG}
      ;;
    f)
      app_port=${OPTARG}
      ;;
    p)
      admin_pw=${OPTARG}
      ;;
    h)
      usage
  esac
done

echo -e "\n###################################################################"
echo -e "### prepairing BASIL Demo for Raspberry Pi Debian "
echo -e "### kill all running podman container\n"
podman stop --all

echo -e "\n### api_server_url = ${api_server_url}"
echo -e "### api port = ${api_port}"
echo -e "### app port = ${app_port}"
echo -e "### admin pw = ${admin_pw}"

echo -e "\n###################################################################"
echo -e "### building api container\n"

podman build \
  --build-arg="ADMIN_PASSWORD=${admin_pw}" \
  --build-arg="API_PORT=${api_port}" \
  -f Containerfile-api-rpi \
  -t basil-api-image-rpi .

echo -e "\n###################################################################"
echo -e "### building app container\n"

podman build \
  --build-arg="API_ENDPOINT=http://${api_server_url}:${api_port}" \
  --build-arg="APP_PORT=${app_port}" \
  -f Containerfile-app \
  -t basil-app-image-rpi .

echo -e "\n###################################################################"
echo -e "### create and mount volumes\n"

list='basil-db-vol basil-ssh-keys-vol basil-tmt-logs-vol'
for element in $list;
do
    exists="$(podman volume exists "${element}")"   # check if volume already exists
    if [ "${exists}" ]; then
       echo "volume $element does not exist"
       podman volume create "${element}"
    else
       echo "volume "${element}" already exists"
    fi
    podman volume mount "${element}"
done

echo -e "\n###################################################################"
echo -e "### start api container\n"

podman run \
   -d \
   --privileged \
   --network=host \
   basil-api-image-rpi

echo -e "\n###################################################################"
echo -e "### start app container\n"

podman run \
   -d \
   --privileged \
   --network=host \
   -v "basil-db-vol:/BASIL-API/db/sqlite3" \
   -v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
   -v "basil-tmt-logs-vol:/var/tmp/tmt" \
   basil-app-image-default

echo -e "\n###################################################################"
echo -e "### list running containers\n"

podman ps

echo -e "\n###################################################################"
echo -e "### start now BASIL via chrome browser: http://${api_server_url}:${app_port}\n"
