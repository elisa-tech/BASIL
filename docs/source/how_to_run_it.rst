.. image:: ../../app/src/app/bgimages/basil_black.svg

How to run it
=================================

------------
Architecture
------------

.. image:: _static/_images/architecture.png
   :alt: BASIL Project Architecture
   :align: center
   :width: 60%

**BASIL** consists of three pieces:

+ A Web Rest API
+ A Web Front End Application
+ A Database (default sqlite)


-----------------
Docker Containers
-----------------

You can deploy BASIL via Docker using Dockerfile-api and Dockerfile-app provided as part of the source code.

Or you can download images built in the [GitHub actions](https://github.com/elisa-tech/BASIL/actions).
Pay attention that those images are built with default value of build argument, as an example the ADMIN user password.
So it is suggested to use those images for evaluation or to modify them, changing critical informations before deploiying a BASIL instance.

# Build the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can build the API project using the Dockerfile-api.

Building this container you will also initialize the database.

If you need to host BASIL on a server you should specify following build argument:

 + API_PORT (default is 5000)

BASIL will be configured with an admin user named **admin**.
You can specify the **admin** user password with the following build argument:

 + ADMIN_PASSWORD (default is **admin**)

Here an example of docker build command:

.. code-block:: bash

   docker build \
      --build-arg="ADMIN_PASSWORD=your-desired-password" \
      --build-arg="API_PORT=1234" \
      -f Dockerfile-api \
      -t basil-api-image .


At the same way you can build the APP project using Dockerfile-app

To be able to reach the API project you need to specify the following build argument:

 + API_ENDPOINT (e.g. http://api-server-it:yourport)
 + APP_PORT

.. code-block:: bash

   docker build \
      --build-arg="API_ENDPOINT=http://api-server-url:yourport" \
      --build-arg="APP_PORT=yourport" \
      -f Dockerfile-app \
      -t basil-app-image .


NOTE: API_ENDPOINT must start with http

# Docker Volumes
^^^^^^^^^^^^^^^^

In order to keep persistent data you can specify following volumes:

.. code-block:: bash

   docker volume create basil-db-vol
   docker volume create basil-ssh-keys-vol
   docker volume create basil-tmt-logs-vol


# Start the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can start the API Container above created with the name **basil-api-image** with the following docker command

.. code-block:: bash

   docker run \
      -d \
      --privileged \
      --network=host \
      -p 0.0.0.0:<API-PORT>:<Your desired value> \
      --mount source=basil-db-vol,target=/BASIL-API/db \
      --mount source=basil-ssh-keys-vol,target=/BASIL-API/api/ssh_keys \
      --mount source=basil-tmt-logs-vol,target=/var/tmp/tmt \
      basil-api-image


the ``--privileged`` options is needed to be able to run fedora container as a possible testing environment inside api container.

You can start the APP Container above created with the name **basil-app-image** with the following docker command

.. code-block:: bash

   docker run \
      -d \
      --network=host \
      -p 0.0.0.0:<APP_PORT>:<Your desired value> \
      basil-app-image


# Check Containers Status
^^^^^^^^^^^^^^^^^^^^^^^^^

You can list running containers with the following docker command

.. code-block:: bash

   docker ps


# Inspect an Image
^^^^^^^^^^^^^^^^^^

You can inspect an image overriding the --entrypoint

.. code-block:: bash

   docker run \
      --interactive \
      --tty \
      --network=host \
      --entrypoint=/bin/bash <YOUR IMAGE>


# Backup BASIL DB from Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only the API project is able to interact with the database and the db and due to that you should refer to the **basil-api** container.
You can copy the db file locally with the following docker command:

.. code-block:: bash

   docker cp basil-api-container:/BASIL-API/db/sqlite3/basil.db </YOUR/LOCAL/LOCATION>

# Stop Containers
^^^^^^^^^^^^^^^^^
You can stop running containers, the one that you can see listed with the **ps** docker command using the following syntax:

.. code-block:: bash

   docker stop <NAME OF THE API CONTAINER>
   docker stop <NAME OF THE APP CONTAINER>



.. toctree::
   :maxdepth: 1
   :caption: Contents:
