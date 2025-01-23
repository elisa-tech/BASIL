#/bin/sh

echo -e "################################"
echo -e "### prepairing BASIL Demo ###"
echo -e "### kill all running podman container ###"
podman stop --all

api_server_url=localhost
api_port=5000
app_port=9000
admin_pw=1234

echo -e "\n### api_server_url = $api_server_url ###"
echo -e "### api port = $api_port ###"
echo -e "### app port = $app_port ###"
echo -e "### admin pw = $admin_pw ###\n"

echo -e "################################"
echo -e "### building api container ###\n"

podman build \
  --build-arg="ADMIN_PASSWORD=$admin_pw" \
  --build-arg="API_PORT=$api_port" \
  -f Containerfile-api \
  -t basil-api-image-default .

echo -e "################################"
echo -e "### building app container ###\n"

podman build \
  --build-arg="API_ENDPOINT=http://$api_server_url:$api_port" \
  --build-arg="APP_PORT=$app_port" \
  -f Containerfile-app \
  -t basil-app-image-default .

echo -e "################################"
echo -e "### create and mount volumes ###\n"

podman volume create basil-db-vol
podman volume create basil-ssh-keys-vol
podman volume create basil-tmt-logs-vol

podman volume mount basil-db-vol
podman volume mount basil-ssh-keys-vol
podman volume mount basil-tmt-logs-vol

echo -e "################################"
echo -e "### start api container ###\n"

podman run \
-d \
--privileged \
--network=host \
basil-api-image-default

echo -e "################################"
echo -e "### start app container ###\n"

podman run \
-d \
--privileged \
--network=host \
-v "basil-db-vol:/BASIL-API/db/sqlite3" \
-v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
-v "basil-tmt-logs-vol:/var/tmp/tmt" \
basil-app-image-default

echo -e "################################"
echo -e "### list running containers ###\n"

podman ps

echo -e "################################"
echo -e "### start now the app via chrome browser: http://$api_server_url:$app_port ###\n"

