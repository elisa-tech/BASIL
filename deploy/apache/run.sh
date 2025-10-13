#!/bin/bash

source .env
source ./common.sh

set -e

echo ===================================================================
echo BASIL Apache Deployment
echo -------------------------------------------------------------------

sudo apt update
packages="curl gnupg postgresql postgresql-contrib libapache2-mod-wsgi-py3 rsync git jq python3 python3-pip python3-venv"
for package in $packages; do
    install_package $package
done
sudo apt autoremove -y && sudo apt clean

bash ./init_postgresql.sh | tee init_postgresql.log
bash ./build_basil_api.sh | tee build_basil_api.log
bash ./build_basil_frontend.sh | tee build_basil_frontend.log
