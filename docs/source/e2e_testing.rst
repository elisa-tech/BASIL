.. image:: ../../app/src/app/bgimages/basil_black.svg

E2E Testing with cypress
========================


-------------
Preconditions
-------------

## 📌 API (Backend)

Before running the e2e testing via cypress you need to

   1. run the BASIL API in testing mode
   2. Set the BASIL ADMIN PASSWORD as specified in the same cypress configuration file.

Here an example running directly the gunicorn webserver:

.. code-block:: bash

   BASIL_ADMIN_PASSWORD=dummy_password BASIL_TESTING=1 TEST_RUNS_BASE_DIR=$(pwd) gunicorn --bind 0.0.0.0:5005 api:app

That will create a test database **db/sqlite3/test.db** preventing the modification of your production db **db/sqlite3/basil.db**

The api port is defined in the test suite at **app/cypress/fixtures/consts.json**.

## 📌 APP (Frontend)

Before running the e2e testing via cypress you need to configure:

   1. the APP port as specified in the cypress configuration file  **app/cypress/fixtures/consts.json**.
      Editing the **PORT** variable defined at **app/webpack.dev.js** accordingly.
   2. the API port as specified in the same cypress configuration file.
      Editing the **API_BASE_URL** variable defined at **app/src/app/Constants/constants.tsx**.

.. code-block:: bash

   cd app
   npm run start:dev


-----------
E2E Testing
-----------

Run Cypress e2e testing in the terminal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From BASIL project root directory:

.. code-block:: bash

   cd app
   npx cypress run


Open the cypress application for interactive Testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From BASIL project root directory:

.. code-block:: bash

   cd app
   npx cypress open


.. toctree::
   :maxdepth: 1
   :caption: Contents:
