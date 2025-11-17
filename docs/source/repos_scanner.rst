Artifacts and Repository Scanner
================================

Overview
--------
The scanner defined in ``api/repos_scanner.py`` extracts structured "traceability"
information from a code/documentation repository based on a YAML configuration.
It can:

- Clone a repository in a per-user temp folder.
- Extract "snippets" (text sections) from an API reference document.
- Derive work items from the snippets:
  - Documents and nested documents
  - Software requirements (and nested)
  - Test specifications
  - Test cases
  - Justifications
- Generate or re-use records in the database for all of the above (traceability generation).


Command Line Interface
----------------------
The module can be executed directly to run a scan using a user's configuration file:

.. code-block:: bash

   python api/repos_scanner.py --userid 2 [--logfile 20251115_120000.log]

- ``--userid``: required. Used to locate the per-user config under
  ``api/user-files/<USERID>.config/config.yaml`` and to generate DB entities under that user.
- ``--logfile``: optional. When omitted, a timestamped log file is created in the same directory.

Logs are written to: ``api/user-files/<USERID>.config/<logfile>``.


User Files and Layout
---------------------
On a scan, the scanner mirrors the API reference document into the user's files:

- Repository is cloned into a per-user temp directory (sanitized path).
- The matching API reference document is copied into
  ``api/user-files/<USERID>/<api>_<branch>.<ext>`` and used for section extraction.


Configuration Primer
--------------------
The main configuration is YAML-based. At the top level:

.. code-block:: yaml

   api:
     - name: ["myApi"]              # one or more API names (expanded as separate runs)
       library: "myLib"
       library_version: "__ref__"   # supports magic variables (branch/ref/version)
       repository:
         url: "https://github.com/org/repo.git"
         branch: "main"
         filename_pattern: "*.md"
         folder_pattern: "docs"
         hidden: false
         file_contains: []          # OR filter: include files containing any
         file_not_contains: []      # OR filter: exclude files containing any
       snippets:
         rules:
           - name: "API Sections"
             section:
               start:
                 line_equal: "START"
                 strip: true
               end:
                 line_equal: "END"
                 strip: true
             # Optional: split/filter/transform (explained below)
             documents: { rules: [...] }
             software_requirements: { rules: [...] }
             test_specifications: { rules: [...] }
             test_cases: { rules: [...] }
             justifications: { rules: [...] }

You can define nested rules (e.g., documents under documents) by supplying a sub-tree with ``rules``.


Section Extraction (start/end)
------------------------------
Sections are identified in two steps:

1) ``start`` selects the starting point(s)
2) ``end`` trims each selected section to its end

Both blocks accept a rich set of matchers (use exactly one per block, or combine with ``closest``):

- ``line_starting_with`` / ``line_not_starting_with``
- ``line_ending_with`` / ``line_not_ending_with``
- ``line_contains`` / ``line_not_contains``
- ``line_equal`` / ``line_not_equal``
- ``line_regex`` (regular expression)
- ``line`` (exact line index) and ``at`` (exact character index)

Common options:

- ``strip`` (bool|string|list-of-chars): default False. When True, trims whitespace; or pass characters.
- ``lstrip`` / ``rstrip``: like ``strip`` but applied only to left/right.
- ``case_sensitive``: default False.
- ``skip_top_items`` / ``skip_bottom_items``: skip matched sections at the beginning/end of the result list.
- ``first_only``: if True, stop after first match in each scanned range.

Closest and Extend
~~~~~~~~~~~~~~~~~~
- ``closest`` can re-anchor a start range to the closest line (e.g., to the nearest header above).
- ``extend`` allows adding lines up/down by a fixed count after a start has been identified.

Example:

.. code-block:: yaml

   section:
     start:
       line_contains: "Title:"
       closest:
         direction: "up"
         line_starting_with: "# "
     end:
       line_starting_with: "## "  # next header
       first_only: true


Filtering (after extraction; before transform)
----------------------------------------------
Once ``start``/``end`` have produced sections, you can filter them:

.. code-block:: yaml

   section:
     start: { line_equal: "START", strip: true }
     end:   { line_equal: "END",   strip: true }
     filter:
       contains: ["keep this"]       # OR of substrings
       not_contains: ["exclude"]     # OR of substrings
       regex: ["\\bID-\\d+\\b"]      # OR of regexes
       case_sensitive: false         # optional, default false

Filtering runs before ``transform``. Elements are kept if:

- they match any of ``contains`` (if provided), and
- they do not match any of ``not_contains`` (if provided), and
- they match any of the ``regex`` (if provided).


Split (optional)
----------------
After end-trimming (and before filter/transform), sections can be split into multiple elements:

.. code-block:: yaml

   section:
     start: { line_equal: "START" }
     end:   { line_equal: "END" }
     split:
       delimiter: "\n---\n"
       strip: true
       keep_empty: false

Each split part becomes a new element with a recalculated index relative to the original text.


Transform (final text changes)
------------------------------
Transforms are applied last (after filtering). Supported operations:

- ``uppercase`` / ``lowercase`` / ``camelcase`` / ``strip``
- ``suffix`` (requires ``value``) / ``prefix`` (requires ``value``)
- ``replace`` (requires ``what`` and ``with``)
- ``regex_sub`` (``what``/``pattern`` and ``with``; flags via ``flags: "ims"`` or booleans:
  ``ignorecase``, ``multiline``, ``dotall``)

Example:

.. code-block:: yaml

   section:
     start: { line_equal: "START", strip: true }
     end:   { line_equal: "END",   strip: true }
     filter:
       contains: ["keep"]
     transform:
       - { how: "regex_sub", what: "\\s+", with: " " }
       - { how: "uppercase" }


Work Item Rules
---------------
Each work item type has a field schema. The scanner will extract values from the reference document (or use constants)
and then combine them to produce items. Highlights:

- Snippets:

  - ``SNIPPET_FIELDS``: ``section`` (str), ``offset`` (int)

- Documents:

  - ``DOCUMENT_FIELDS``: ``title``, ``description``, ``document_type``, ``spdx_relation``, ``url``, ``coverage``
  - Supports nested documents (``documents.rules``)

- Software Requirements:

  - ``SOFTWARE_REQUIREMENT_FIELDS``: ``title``, ``description``, ``coverage``
  - Supports nested software requirements, test specifications, test cases

- Test Specifications:

  - ``TEST_SPECIFICATION_FIELDS``: ``title``, ``preconditions``, ``test_description``,
    ``expected_behavior``, ``coverage``

- Test Cases:

  - ``TEST_CASE_FIELDS``: ``title``, ``description``, ``repository`` (optional), ``relative_path`` (optional),
    ``coverage``

For each rule, you can use constants (``value``) or extraction (``start``/``end``) per field. Lists must align in
length; otherwise the rule is skipped.


Traceability Generation
-----------------------
``TraceabilityGenerator`` walks the extracted traceability structure and:

- Creates or reuses DB entities (APIs, Documents, Software Requirements, Test Specifications, Test Cases, Justifications).
- Persists mappings and nested relations.
- Commits per step for robustness.

It uses the logged-in user (``--userid``) as creator for all new entities.


Notes and Recommendations
-------------------------
- For exact string comparisons on lines, prefer ``strip: true`` to normalize whitespace.
- Use ``first_only`` to prevent multiple end matches within the same element.
- ``skip_top_items``/``skip_bottom_items`` can be set independently for start and end.
- Filtering is case-insensitive by default; set ``case_sensitive: true`` if needed.
- For nested rules, remember each nested block is itself a full ruleset with its own ``repository`` and field configs.
