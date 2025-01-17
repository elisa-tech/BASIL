.. image:: ../../app/src/app/bgimages/basil_black.svg

E2E Testing with cypress
========================


-------------
Preconditions
-------------

Before running the e2e testing via cypress you need to run the api project with the **--testing** option.

From BASIL project root directory:

.. code-block:: bash

   pdm run api/api.py --testing


That will create a test database **db/test.db** preventing the modification of your production db **db/sqlite3/basil.db**


-----------
E2E Testing
-----------

Run Cypress e2e testing in the terminal
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From BASIL project root directory:

.. code-block:: bash

   npx cypress run


Open the cypress application for interactive Testing
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

From BASIL project root directory:

.. code-block:: bash

   npx cypress open


.. toctree::
   :maxdepth: 1
   :caption: Contents:
