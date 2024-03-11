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

# Build the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can build the API project using the Dockerfile-api.

Building this container you will also initialize the database.

If you need to host BASIL on a server you should specify following build argument:

 + API_PORT (default is 5000)

BASIL will be configured with an admin user name **admin**.
You can specify the **admin** user password with the following build argument:

 + ADMIN_PASSWORD (default is **admin**)

Here an example of docker build command:

``docker build --build-arg ADMIN_PASSWORD=your-desired-password --build-arg API_PORT=1234 -f Dockerfile-api -t basil-api-image .``

At the same way you can build the APP project using Dockerfile-app

To be able to reach the API project you need to specify the following build argument:

 + API_ENDPOINT (e.g. http://api-server-it:yourport or http://api-server-it/reverse-proxy-route)

``docker build --build-arg API_ENDPOINT=http://api-server-it:yourport -f Dockerfile-app -t basil-app-image .``

NOTE: API_ENDPOINT must start with http

# Start the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can start the API Container above created with the name **basil-api-image** with the following docker command

``docker run -d --network=host --name basil-api-container basil-api-image``

You can start the APP Container above created with the name **basil-app-image** with the following docker command

``docker run -d --network=host --name basil-app-container basil-app-image``

# Check Containers status
^^^^^^^^^^^^^^^^^^^^^^^^^

You can list running containers with the following docker command

``docker ps``

# Backup BASIL DB from Container
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Only the API project is able to interact with the database and the db and due to that you should refer to the **basil-api** container.
You can copy the db file locally with the following docker command:

``docker cp basil-api-container:/BASIL-API/db/basil.db </YOUR/LOCAL/LOCATION>``

# Stop Containers
^^^^^^^^^^^^^^^^^
You can stop running containers, the one that you can see listed with the **ps** docker command using the following syntax:

``docker stop basil-api-container``

``docker stop basil-app-container``


---------------------
Manual Configurations
---------------------

In case you don't want to use containers you can configure BASIL environment manually.

Here following few useful information to be able to set it up correctly.

Init the database
^^^^^^^^^^^^^^^^^
BASIL comes without a database and is up to the user to init it.
The default configuration is based on an sqlite database.
It is possible to use a different type of database configuring the SQLAlchemy create_engine method used in in the **db/db_orm.py** script.

To be able to create an admin user at database initialization you should specify the following environment variable:

 + BASIL_ADMIN_PASSWORD (populated with your desired admin password)

This way you will be able to login in BASIL with **admin** and you desired admin password.

Move to the db/models directory

``cd db && cd models``

Initialize the sqlite database

``python3 init_db.py``

That will create the sqlite3 database at **db/basil.db**


Navigate the database
^^^^^^^^^^^^^^^^^^^^^

To be able to read the database you need a tool like **sqlite3**.

Here following some useful sqlite commands:

- List all the tables:
``.table``

- Analyze a table schema
``.schema <table>``


----------
API
----------

Install api dependencies via pdm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To know more about how to install pdm, click `here <https://pdm-project.org/latest/#installation>`_.

From BASIL project root directory:

``pdm install``

Start the Flask Server
^^^^^^^^^^^^^^^^^^^^^^

The Flask Server is suggested only for development.
For production it is suggested to use a WSGI server instead like gunicorn.

From BASIL project root directory:

``pdm run python3 api/api.py``

As default BASIL is configured to work on your local machine and to be used from your machine only.
API will starts on port 5000 and it will be available in the network if your firewall allow it.
To be able to edit the port you should edit following files:

+ api/api_url.py - variable **api_port**
+ app/src/app/Constants/constants.tsx - variable **API_BASE_URL**


-------------
Front End APP
-------------

The UI was built using the `patternfly-react-seed <https://github.com/patternfly/patternfly-react-seed>`_

Install app dependencies via npm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``npm install``


Run the development server
^^^^^^^^^^^^^^^^^^^^^^^^^^

``npm run start:dev``


Run a production build (outputs to "dist" dir)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``npm run build``


# Run the linter
^^^^^^^^^^^^^^^^
``npm run lint``


# Run the code formatter
^^^^^^^^^^^^^^^^^^^^^^^^
``npm run format``


# Launch a tool to inspect the bundle size
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``npm run bundle-profile:analyze``


# Start the express server (run a production build first)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``npm run start``




.. toctree::
   :maxdepth: 1
   :caption: Contents:
