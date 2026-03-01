.. image:: ../../app/src/app/bgimages/basil_black.svg

Custom Actions
==============

BASIL allows users and admins to define custom actions for different work item types.

The actions defined by an admin are available for all users.
The actions defined by a user are available only for the user.

The actions are defined in the following way in a setting yaml file:

.. code-block:: yaml
actions:
  api:
    - name: "Action Name"
        label: "Action Button Label"
        alt: "Action Button Alternative Text"
        type: http
        config:
          url: "https://www.example.com"
          method: "GET"
          headers:
            - "Content-Type: application/json"
          body:
            - "key: value"
  sw_requirement:
      ...
  test_specification:
      ...
  test_case:
      ...
  justification:
      ...
  document:
      ...

.. toctree::
   :maxdepth: 1
   :caption: Contents:
