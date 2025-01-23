#/bin/sh

echo -e "\n### prepairing BASIL Demo ###\n"

api_server_url=localhost
api_port=5000
app_port=9000

echo -e "\n### api_server_url = $api_server_url ###\n"
echo -e "\n### api port = $api_port ###\n"
echo -e "\n### app port = $app_port ###\n"

echo -e "\n### building api container ###\n"

podman build \
  --build-arg="ADMIN_PASSWORD=admin" \
  --build-arg="API_PORT=$api_port" \
  -f Containerfile-api \
  -t basil-api-image-default .

echo -e "\n### building app container ###\n"

podman build \
  --build-arg="API_ENDPOINT=http://$api_server_url:$api_port" \
  --build-arg="APP_PORT=$app_port" \
  -f Containerfile-app \
  -t basil-app-image-default .

echo -e "\n### create and mount volumes ###\n"

podman volume create basil-db-vol
podman volume create basil-ssh-keys-vol
podman volume create basil-tmt-logs-vol

podman volume mount basil-db-vol
podman volume mount basil-ssh-keys-vol
podman volume mount basil-tmt-logs-vol

echo -e "\n### start api container ###\n"

podman run \
-d \
--privileged \
--network=host \
basil-api-image-default

echo -e "\n### start app container ###\n"

podman run \
-d \
--privileged \
--network=host \
-v "basil-db-vol:/BASIL-API/db/sqlite3" \
-v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
-v "basil-tmt-logs-vol:/var/tmp/tmt" \
basil-app-image-default

echo -e "\n### list running containers ###\n"

podman ps

echo -e "\n### start now the app via chrome browser: http://$api_server_url:$app_port ###\n"

