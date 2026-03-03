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

Where in case of method GET:
- blank: true || undefined  means that the action will be opened in a new tab
- blank: false means that the action will be created in the current tab and the response will be displayed into an alert dialog

In case of method POST, PUT, DELETE, PATCH the request will be sent to the URL and the response will be displayed into an alert dialog

.. toctree::
   :maxdepth: 1
   :caption: Contents:
