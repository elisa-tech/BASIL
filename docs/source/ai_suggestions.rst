.. _ai_suggestions:

In-app AI suggestions
=====================

BASIL can use an OpenAI-compatible API to suggest content for work items directly in the app.
The backend module :file:`api/ai.py` provides an :class:`AIPrompter` that calls the configured AI service to generate:

- **Software requirement metadata** — title, description, completeness, and reasoning from a specification excerpt
- **Test case metadata** — title, description, completeness, and reasoning for a test case from a specification
- **Test specification metadata** — title, preconditions, test description, expected behavior, completeness, and reasoning
- **Test case implementation** — a single-file implementation proposal (saved under :file:`api/user-files/<user_id>/`)

The app uses these suggestions when creating or editing Software Requirements, Test Specifications, and Test Cases, so users can get AI-drafted fields from the selected specification text.


Configuration
^^^^^^^^^^^^^

AI is configured via:

1. The admin **settings** (recommended for host, port, model, etc.)
2. **Environment variables** (override or supply values when the settings file does not) of API deployment

Admin Settings
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 60 20

   * - Option
     - Description
     - Required
   * - ``host``
     - Base URL of the AI API (e.g. ``https://api.openai.com`` or ``http://localhost:1234``). Do not include path or trailing slash.
     - Yes
   * - ``port``
     - Port number (e.g. ``443`` for HTTPS, or the port of your local server).
     - Yes
   * - ``model``
     - Model name (e.g. ``gpt-4o``, ``phi3.5``, or the identifier of your local model).
     - Yes
   * - ``api_version``
     - API version path segment (default: ``v1``). Prepended to the path used for chat completions.
     - No (default: ``v1``)
   * - ``temperature``
     - Sampling temperature (0–1). Lower values give more deterministic output. Default: ``0``.
     - No (default: ``0``)
   * - ``token``
     - API key or token for authentication. Use for services that require it (e.g. OpenAI). Can be left empty for local servers without auth.
     - No
   * - ``max_tokens``
     - Maximum tokens for each AI response. If the model truncates output (e.g. "Invalid JSON: EOF while parsing"), increase this. Default: ``4096``.
     - No (default: ``4096``)

Example:

.. code-block:: yaml

   ai:
     host: "https://api.openai.com"
     port: 443
     model: "gpt-4o"
     api_version: "v1"
     temperature: 0
     token: "sk-..."


Environment variables
^^^^^^^^^^^^^^^^^^^^^

You can override or supply AI configuration via environment variables. These are used when the corresponding key is missing (or not set) in the settings file.

.. list-table::
   :header-rows: 1
   :widths: 30 50

   * - Variable
     - Purpose
   * - ``BASIL_AI_HOST``
     - Same as ``ai.host``
   * - ``BASIL_AI_PORT``
     - Same as ``ai.port``
   * - ``BASIL_AI_MODEL``
     - Same as ``ai.model``
   * - ``BASIL_AI_API_VERSION``
     - Same as ``ai.api_version``
   * - ``BASIL_AI_TEMPERATURE``
     - Same as ``ai.temperature``
   * - ``BASIL_AI_TOKEN``
     - Same as ``ai.token``
   * - ``BASIL_AI_MAX_TOKENS``
     - Same as ``ai.max_tokens``

Example:

.. code-block:: bash

   export BASIL_AI_HOST="https://api.openai.com"
   export BASIL_AI_PORT=443
   export BASIL_AI_MODEL="gpt-4o"
   export BASIL_AI_TOKEN="sk-..."

Validation and health check
--------------------------

- On each AI request, the backend checks that **host**, **port**, and **model** are set (via settings or environment). If any is missing, the API returns a precondition failed response and the in-app suggestion feature will not call the AI.
- A **health check** endpoint (used by the app to verify AI availability) calls ``GET {base_url}/models``. The AI service must respond with HTTP 200 for the app to consider the AI feature available.

API endpoints (reference)
-------------------------

The following REST resources are used by the app for AI suggestions:

- **AI health check** — GET endpoint to verify the configured AI service is reachable.
- **Suggest software requirement metadata** — POST with ``spec``; returns title, description, completeness, reasoning.
- **Suggest test case metadata** — POST with ``spec``; returns title, description, completeness, reasoning.
- **Suggest test specification metadata** — POST with ``spec``; returns title, preconditions, test description, expected behavior, completeness, reasoning.
- **Suggest test case implementation** — POST with ``spec`` and ``title``; returns implementation text and a file path under :file:`api/user-files/<user_id>/`.

All suggestion endpoints require a valid API user with write permission.

See the main API documentation or :file:`api/api.py` for the exact routes and request/response formats.
