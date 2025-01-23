#/bin/sh

echo -e "\n### prepairing BASIL Demo ###\n"

echo -e "\n### pbuilding api container ###\n"

podman build \
  -f Containerfile-api \
  -t basil-api-image-default .

echo -e "\n### pbuilding app container ###\n"

podman build \
  -f Containerfile-app \
  -t basil-app-image-default .

echo -e "\n### pcreate and mount volumes ###\n"

podman volume create basil-db-vol
podman volume create basil-ssh-keys-vol
podman volume create basil-tmt-logs-vol

podman volume mount basil-db-vol
podman volume mount basil-ssh-keys-vol
podman volume mount basil-tmt-logs-vol

echo -e "\n### pstart api container ###\n"

podman run \
-d \
--privileged \
--network=host \
basil-api-image-default

echo -e "\n### pstart app container ###\n"

podman run \
-d \
--privileged \
--network=host \
-v "basil-db-vol:/BASIL-API/db/sqlite3" \
-v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
-v "basil-tmt-logs-vol:/var/tmp/tmt" \
basil-app-image-default

echo -e "\n### plist running containers ###\n"

podman ps

echo -e "\n### start now the app via chrome browser: http://localhost:9000/ ###\n"

