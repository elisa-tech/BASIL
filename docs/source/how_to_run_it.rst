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

`run_demo.sh` is a script that can be used to deploy a BASIL instance.
It comes with a default configuration but relevant parameters can be changed using different arguments.
To see all the possible parameters that can be changed, run the following command:

.. code-block:: bash

   ./run_demo.sh -h

Here and example command to deploy BASIL using Debian on a Raspberry Pi that is available at the ip 192.168.1.13 in a local netowork with API running on port 5005, APP running on port 9005, and admin password eqaul to **dummy_password**

.. code-block:: bash
   
   sudo ./run_demo.sh -b 5005 -f 9005 -d debian -p 'dummy_password' -u http://192.168.1.13

Here and example command to deploy BASIL for evaluation on localhost with default configuration.

.. code-block:: bash

   sudo ./run_demo.sh

In this case API will run on port 5000, APP on port 9000 and admin default password is **1234**.

It is also possible to injet environemnt variables selecting an .env file with the **-e** option.
In the following example we are injecting all the environment variables defined in the **prod.env** file into the container running the api:

.. code-block:: bash

   sudo ./run_demo -b 5005 -f 9005 -d debian -p 'dummy_password' -u http://192.168.1.13 -e prod.env

Those environment variables can be used by an admin user to populate test plugin preset configuration variables and general tool setting as the email server password.

BASIL can be also deployed manually building Containerfile-api-fedora (or Containerfile-api-debian) and Containerfile-app provided as part of the source code.

# Build the Containers
^^^^^^^^^^^^^^^^^^^^^^

The API project can be built using the Containerfile-api-fedora (or Container-file-debian) file.

This process will also initialize the database.
BASIL default configuration will start the api project on the port 5000 and will
create an ADMIN user with name **admin** and password **admin**.

.. code-block:: bash

   podman build \
      -f Containerfile-api-fedora \
      -t basil-api-image-default .

You can customize your container, configuring a different port and admin password using following 
build arguments:

 + API_PORT (default is 5000)
 + ADMIN_PASSWORD (default is **admin**) 

Here an example of a build command for a custom container:

.. code-block:: bash

   podman build \
      --build-arg="ADMIN_PASSWORD=your-desired-password" \
      --build-arg="API_PORT=1234" \
      -f Containerfile-api-fedora \
      -t basil-api-image .

At the same way you can build the APP project using Containerfile-app

The default configuration will start the web application on the port 9000 and 
will try to communicate with the api project on the port 5000.

.. code-block:: bash

   podman build \
      -f Containerfile-app \
      -t basil-app-image-default .


You can customize your container specifying a differnt api endpoint and application port
using the following build arguments:

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

   podman volume create basil-configs-vol
   podman volume create basil-db-vol
   podman volume create basil-ssh-keys-vol
   podman volume create basil-tmt-logs-vol
   podman volume create basil-user-files-vol

   podman volume mount basil-configs-vol
   podman volume mount basil-db-vol
   podman volume mount basil-ssh-keys-vol
   podman volume mount basil-tmt-logs-vol
   podman volume mount basil-user-files-vol


# Start the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can start the api default container above created with the following command:

.. code-block:: bash

  podman run \
    -d \
    --privileged \
    --network=host \
    basil-api-image-default


Here an example of usage of volumes:

.. code-block:: bash

  podman run \
    -d \
    --privileged \
    --network=host \
    -v "basil-configs-vol:/BASIL-API/api/configs" \
    -v "basil-db-vol:/BASIL-API/db/sqlite3" \
    -v "basil-ssh-keys-vol:/BASIL-API/api/ssh_keys" \
    -v "basil-user-files-vol:/BASIL-API/api/user-files" \
    -v "basil-tmt-logs-vol:/var/tmp/tmt" \
    basil-api-image


the ``--privileged`` options is needed to be able to run fedora (or debian) container as a possible testing environment inside api container.

You can start the app default container above created with the following command

.. code-block:: bash

   podman run \
      -d \
      --network=host \
      basil-app-image-default


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

Once you are inside the api container you can, as an example, read the database to check your data.
To do that you need to install **sqlite3** that is not installed by default and then
connect to the db:

.. code-block:: bash

   dnf install -y sqlite3
   sqlite3 db/sqlite3/basil.db


# Backup BASIL DB from Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

BASIL default sqlite3 database is part of the API project and due to that you should refer to the **basil-api** container.
You can copy the db file locally with the following command:

.. code-block:: bash

   podman cp basil-api-container:/BASIL-API/db/sqlite3/basil.db </YOUR/LOCAL/LOCATION>

or you can backup the podman volume if you have configured it

.. code-block:: bash

   podman volume export basil-db-vol --output basil-db-vol_$(date '+%Y%m%d_%H%M').tar

We also provide a cronjob in the **misc/cronjobs/daily** folder that can be installed in the **/etc/cron.daily** folder of 
the machine running the api container to automatically backup the database volume each day.

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
