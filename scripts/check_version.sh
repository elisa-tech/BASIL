#!/bin/bash

# To be executed from BASIL root folder

PYPROJECT_VERSION=$(cat pyproject.toml| grep "^version" | cut -d "=" -f 2 | sed "s/\"//g")
APP_CONSTANTS_VERSION=$(cat app/src/app/Constants/constants.tsx| grep BASIL_VERSION | cut -d "=" -f 2 | sed "s/'//g")

echo "pyproject.toml version: ${PYPROJECT_VERSION}"
echo "app/src/app/Constants/constants.tsx version: ${APP_CONSTANTS_VERSION}"

if [ $PYPROJECT_VERSION != $APP_CONSTANTS_VERSION ]; then
  echo "Error"
  exit 1
else
  echo "OK"
fi