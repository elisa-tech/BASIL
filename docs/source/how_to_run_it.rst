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
Podman Containers
-----------------

You can deploy BASIL via podman using Containerfile-api and Containerfile-app provided as part of the source code.

Or you can download images built in the [GitHub actions](https://github.com/elisa-tech/BASIL/actions).
Pay attention that those images are built with default value of build argument, as an example the ADMIN user password.
So it is suggested to use those images for evaluation or to modify them, changing critical informations before deploiying a BASIL instance.

# Build the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can build the API project using the Containerfile-api.

Building this container you will also initialize the database.

If you need to host BASIL on a server you should specify following build argument:

 + API_PORT (default is 5000)

BASIL will be configured with an admin user named **admin**.
You can specify the **admin** user password with the following build argument:

 + ADMIN_PASSWORD (default is **admin**)

Here an example of podman container build command:

.. code-block:: bash

   podman build \
      --build-arg="ADMIN_PASSWORD=your-desired-password" \
      --build-arg="API_PORT=1234" \
      -f Containerfile-api \
      -t basil-api-image .


At the same way you can build the APP project using Containerfile-app

To be able to reach the API project you need to specify the following build argument:

 + API_ENDPOINT (e.g. http://api-server-it:yourport)
 + APP_PORT

.. code-block:: bash

   podman build \
      --build-arg="API_ENDPOINT=http://api-server-url:yourport" \
      --build-arg="APP_PORT=yourport" \
      -f Containerfile-app \
      -t basil-app-image .


NOTE: API_ENDPOINT must start with http

# Volumes
^^^^^^^^^

In order to keep persistent data across deployments you can specify following volumes:

.. code-block:: bash

   podman volume create basil-db-vol
   podman volume create basil-ssh-keys-vol
   podman volume create basil-tmt-logs-vol

   podman volume mount basil-db-vol
   podman volume mount basil-ssh-keys-vol
   podman volume mount basil-tmt-logs-vol


# Start the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can start the API Container above created with the name **basil-api-image** with the following command

.. code-block:: bash

  podman run \
    -d \
    --privileged \
    --network=host \
    -v "basil-db-vol:/BASIL-API/db/sqlite3" \
    -v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
    -v "basil-tmt-logs-vol:/var/tmp/tmt" \
    --name basil-api-container \
    basil-api-image


the ``--privileged`` options is needed to be able to run fedora container as a possible testing environment inside api container.

You can start the APP Container above created with the name **basil-app-image** with the following command

.. code-block:: bash

   podman run \
      -d \
      --network=host \
      --name basil-app-container \ 
      basil-app-image


# Check Containers Status
^^^^^^^^^^^^^^^^^^^^^^^^^

You can list running containers with the following command

.. code-block:: bash

   podman ps


# Inspect an Image
^^^^^^^^^^^^^^^^^^

You can inspect an image overriding the --entrypoint

.. code-block:: bash

   podman run \
      --interactive \
      --tty \
      --network=host \
      --entrypoint=/bin/bash <YOUR IMAGE>


# Backup BASIL DB from Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only the API project is able to interact with the database and due to that you should refer to the **basil-api** container.
You can copy the db file locally with the following command:

.. code-block:: bash

   podman cp basil-api-container:/BASIL-API/db/sqlite3/basil.db </YOUR/LOCAL/LOCATION>

# Stop Containers
^^^^^^^^^^^^^^^^^
You can stop running containers, the one that you can see listed with the **ps** command using the following syntax:

.. code-block:: bash

   podman stop <NAME OF THE API CONTAINER>
   podman stop <NAME OF THE APP CONTAINER>


NOTE: above mentioned commands are tested on fedora 37 x86_64 virutal machine with podman version 4.2.1

.. toctree::
   :maxdepth: 1
   :caption: Contents:
