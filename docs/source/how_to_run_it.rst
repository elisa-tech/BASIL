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

Initialize the sqlite database, you will find it in db/basil.db

``python3 init_db.py``


.. toctree::
   :maxdepth: 1
   :caption: Contents:
