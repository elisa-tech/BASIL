.. image:: ../../app/src/app/bgimages/basil_black.svg

Settings
========

BASIL admins can configure the instance from the **Settings** page in the left side menu.
The page is available only to users with the **ADMIN** role.

The page shows a text editor with the content of the file :file:`api/configs/settings.yaml`.
The content is validated as YAML when you save it; invalid YAML is rejected and the file is not changed.

Changes are applied without restarting the API: the file is reloaded every time its modification date changes.

Overview
^^^^^^^^

The default settings file looks like this:

.. code-block:: yaml

   app_url: http://localhost:9000
   smtp:
     from: "BASIL - The FuSa Spice"
     host: ""
     password: ""
     port: 0
     user: ""
     ssl: true
     reply_to: ""
   ai:
     host: ""
     port: 0
     model: ""
     temperature: 0
     token: ""
   actions:
     api:
     sw_requirement:
     test_specification:
     test_case:
     justification:
     document:

The top-level keys are:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Purpose
   * - ``app_url``
     - Public URL of the BASIL web app. See `app_url`_.
   * - ``smtp``
     - Email server used to send notifications. See `smtp`_.
   * - ``ai``
     - AI service used for in-app suggestions. See :ref:`ai_suggestions`.
   * - ``actions``
     - Custom action buttons shown on work items. See `actions`_.
   * - ``alert``
     - Messages shown as a banner to every user. See `alert`_.

Keys that are not listed here are ignored.


app_url
^^^^^^^

Public URL of the BASIL web app, for example ``https://basil.example.com``.

It is used:

- to add a link to the BASIL instance at the bottom of the emails sent by BASIL
- to redirect the user to the BASIL login page after a password reset

If it is empty, emails are sent without the link and the password reset does not redirect to the app.

.. code-block:: yaml

   app_url: https://basil.example.com


smtp
^^^^

Configuration of the SMTP server used to send emails. BASIL sends an email:

- to the admins, when a new user signs up
- to the owners of a Software Component, when a user asks for write permission on it
- to a user, on password reset
- to a user, when an admin changes their role

.. list-table::
   :header-rows: 1
   :widths: 15 55 15 15

   * - Option
     - Description
     - Required
     - Environment variable
   * - ``from``
     - Sender shown in the emails, for example ``"BASIL - The FuSa Spice"``.
     - Yes
     - ``BASIL_SMTP_FROM``
   * - ``host``
     - SMTP server hostname, for example ``smtp.example.com``.
     - Yes
     - ``BASIL_SMTP_HOST``
   * - ``port``
     - SMTP server port, for example ``465`` with SSL or ``587`` with STARTTLS.
     - Yes
     - ``BASIL_SMTP_PORT``
   * - ``user``
     - Username used to log in to the SMTP server.
     - Yes
     - ``BASIL_SMTP_USER``
   * - ``password``
     - Password used to log in to the SMTP server.
     - Yes
     - ``BASIL_SMTP_PASSWORD``
   * - ``ssl``
     - ``true`` connects with SSL from the start (SMTPS, usually port ``465``).
       ``false`` connects in plain text and upgrades with STARTTLS (usually port ``587``).
     - No
     - ``BASIL_SMTP_SSL``
   * - ``reply_to``
     - Address added as ``Reply-To`` header. Left out if empty.
     - No
     - ``BASIL_SMTP_REPLY_TO``

If any required option is missing or empty, BASIL does not send emails and logs which option is not configured.

.. code-block:: yaml

   smtp:
     from: "BASIL - The FuSa Spice"
     host: smtp.example.com
     port: 465
     user: basil@example.com
     password: !ENV ${BASIL_SMTP_PASSWORD}
     ssl: true
     reply_to: basil-admins@example.com


ai
^^

Configuration of the OpenAI-compatible service used for in-app AI suggestions.
The options (``host``, ``port``, ``model``, ``api_version``, ``temperature``, ``token``, ``max_tokens``)
and their environment variables are described in :ref:`ai_suggestions`.


actions
^^^^^^^

Custom actions defined by the admin, available to all users.
Actions are grouped by work item type: ``api``, ``sw_requirement``, ``test_specification``,
``test_case``, ``justification`` and ``document``.
An empty work item type means that no custom action is defined for it.

The format of each action is described in the :doc:`custom_actions` page.


alert
^^^^^

Messages shown as a banner at the top of the Software Components page and of the mapping page, visible to every user.
Use them, for example, to announce a planned maintenance.

Messages are grouped by type, that defines the color of the banner:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Type
     - Banner
   * - ``danger``
     - Red
   * - ``warning``
     - Orange
   * - ``info``
     - Blue
   * - ``success``
     - Green

Each type accepts a list of messages. The key is not present in the default file.

.. code-block:: yaml

   alert:
     warning:
       - "BASIL will be unavailable on Friday from 18:00 to 20:00 for maintenance."
     info: []
     danger: []
     success: []

Open pages check for new messages every 60 seconds.

Alerts can also be added and removed with the ``/alert`` REST endpoint (``POST`` and ``DELETE``, ADMIN only).


Environment variables
^^^^^^^^^^^^^^^^^^^^^

There are two ways to use environment variables of the API deployment.

Fallback for smtp and ai options
--------------------------------

``smtp`` and ``ai`` options that are **not present** in the settings file are read from the matching environment variable
(listed in the `smtp`_ table and in :ref:`ai_suggestions`).

.. warning::

   An option that is present with an empty value (for example ``host: ""``) counts as set:
   BASIL uses the empty value and ignores the environment variable.
   The default settings file defines all the options with empty values, so to use environment variables
   remove the matching lines from the file.

   .. code-block:: yaml

      smtp:
        from: "BASIL - The FuSa Spice"
        ssl: true
        # host, port, user and password are read from
        # BASIL_SMTP_HOST, BASIL_SMTP_PORT, BASIL_SMTP_USER and BASIL_SMTP_PASSWORD

``!ENV`` placeholders
---------------------

Any value in the file can be read from an environment variable with the ``!ENV`` tag.
This is useful to keep secrets such as passwords and tokens out of the file:

.. code-block:: yaml

   smtp:
     password: !ENV ${BASIL_SMTP_PASSWORD}
   ai:
     token: !ENV ${BASIL_AI_TOKEN}
     host: !ENV https://${AI_HOSTNAME}
     model: !ENV ${BASIL_AI_MODEL:gpt-4o}

- ``${NAME:default}`` uses ``default`` when ``NAME`` is not set.
- A variable that is not set and has no default becomes the text ``N/A``, not an empty value.


.. toctree::
   :maxdepth: 1
   :caption: Contents:
