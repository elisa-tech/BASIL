#/bin/sh

echo -e "\n###################################################################"
echo -e "### prepairing BASIL Demo"
echo -e "### kill all running podman container\n"
podman stop --all

echo -e "\n###################################################################"
echo -e "### building api container\n"

podman build \
  -f Containerfile-api \
  -t basil-api-image-default .

echo -e "\n###################################################################"
echo -e "### building app container\n"

podman build \
  -f Containerfile-app \
  -t basil-app-image-default .

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
   basil-api-image-default

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
echo -e "### start now the app via chrome browser: http://localhost:9000/\n"

