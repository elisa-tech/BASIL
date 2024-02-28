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

--------
Database
--------

Init the database
^^^^^^^^^^^^^^^^^
BASIL comes without a database and is up to the user to init it.
The default configuration is based on an sqlite database.
It is possible to use a different type of database configuring the SQLAlchemy create_engine method used in in the **db/db_orm.py** script.


Move to the db/models directory

``cd db && cd models``

Defining the environment variable BASIL_ADMIN_PASSWORD you will be able to create an ADMIN user, during the database initialization, with the desired credentials.

Initialize the sqlite database, you will find it in db/basil.db

``python3 init_db.py``


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
For production it is suggested to use a WSGI server instead.

From BASIL project root directory:

``pdm run python3 api/api.py``

As default BASIL is configured to work on your local machine and to be used from your machine only.
API will starts on port 5000 and it will be available in the network if your firewall allow it.
To be able to edit the port you should edit following files:

+ api/api_url.py - variable **api_port**
+ app/src/app/Constants/constants.tsx - variable **API_BASE_URL**

**IMPORTANT**
If you want to configure BASIL to be used from multiple clients, or in general, if you want to host BASIL on a different machine from the one that call it, you should setup above mentioned files with the ip address of the server machine.

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


-----------------
Docker Containers
-----------------

You can deploy BASIL via Docker using Dockerfile-api and Dockerfile-app provided as part ofthe source code.
Before building your container, if you need to access BASIL from a machine different from the one that is hosting it, you need to specify the following arguments in the docker command:

 + **BASIL_HOSTNAME** (name of the host machine or ip address)
 + **BASIL_API_PORT** (number of the port you want to assign to the API)

# Build the Containers
^^^^^^^^^^^^^^^^^^^^^^

You can build the API project using the Dockerfile-api with the following command

``docker build --build-arg BASIL_ADMIN_PASSWORD=your-desired-password --build-arg BASIL_HOSTNAME=basil.server.com --build-arg BASIL_API_PORT=1234 -f Dockerfile-api -t basil-api-image .``

At the same way you can build the APP project using Dockerfile-app

``docker build --build-arg BASIL_HOSTNAME=basil.server.com --build-arg BASIL_API_PORT=1234 -f Dockerfile-app -t basil-app-image .``


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

``docker stop basil-api-containeri``
``docker stop basil-app-containeri``



.. toctree::
   :maxdepth: 1
   :caption: Contents:
