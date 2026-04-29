.. image:: ../../app/src/app/bgimages/basil_black.svg

Mapping Views
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


--------
Overview
--------

When you open a Software Component, BASIL displays the Mapping page.
At the top of the page a **Mapping view** dropdown lets you choose how the reference document and its work items are presented.

Each view is designed for a different purpose.
The type-specific views (Sw Requirements, Test Specifications, Test Cases, Justifications Only) let you focus on one work item type at a time.
The Dynamic View gives a cross-type overview of the whole specification coverage.
The Raw Specification view shows the reference document as plain text without any mapping information.

Two switches are also available at the top of the page:

+ **Indirect Test Specification**: when enabled, Test Specifications that are nested under a Software Requirement are shown in the view.
+ **Indirect Test Case**: when enabled, Test Cases that are nested under a Software Requirement or a Test Specification are shown in the view.


---------------------------------------------
Type-Specific Views (Mapped / Unmapped Split)
---------------------------------------------

The views **Sw Requirements**, **Test Specifications**, **Test Cases**, and **Justifications Only** share the same layout.

They split the reference document into two lists:

+ **Mapped sections**: portions of the specification that have at least one work item of the selected type directly mapped to them. Each section shows the specification text and the associated work items.
+ **Unmapped sections**: portions of the specification that do not have any work item of the selected type directly mapped to them. These sections show only the specification text.

The key concept is that selecting a particular view focuses on work items with a **direct** mapping to the reference document.
For example, a Test Case directly mapped to a section of the specification is only visible in the **Test Cases** view.
The same Test Case can also appear in the **Sw Requirements** view if it is nested under a Software Requirement, but in that case it is shown as an indirect child.

This design allows different teams and workflows to use only the work item types they need.
If a user only wants to create Test Cases and map them to the specification, that is perfectly fine and the **Test Cases** view will show everything that matters.

Sw Requirements
^^^^^^^^^^^^^^^

Shows Software Requirements directly mapped to the specification.
Each mapped section displays the related Software Requirement cards with their title, description, status, version, and coverage.
When indirect switches are enabled, nested Test Specifications and Test Cases appear indented below the parent Software Requirement.

Test Specifications
^^^^^^^^^^^^^^^^^^^

Shows Test Specifications directly mapped to the specification.
Each mapped section displays the related Test Specification cards with their title, preconditions, test description, expected behavior, status, and version.
When the indirect Test Case switch is enabled, nested Test Cases appear indented below the parent Test Specification.

Test Cases
^^^^^^^^^^

Shows Test Cases directly mapped to the specification.
Each mapped section displays the related Test Case cards with their title, description, status, version, and a link to the test implementation.

Justifications Only
^^^^^^^^^^^^^^^^^^^

Shows Justifications directly mapped to the specification.
This view is useful to highlight which sections of the specification cannot or should not be related to other work item types and to document the reason why.


-----------------
Raw Specification
-----------------

The **Raw Specification** view shows the full reference document as plain text.
No mapping information is displayed and no work items are shown.
This is useful to read the specification without any overlay or to select a section before creating a new work item.


------------
Dynamic View
------------

The **Dynamic View** takes a different approach compared to the type-specific views.
Instead of splitting the specification by mapped and unmapped sections for a single work item type, it displays the full reference document alongside **all** directly mapped work items of every type in a unified two-column layout.


Why the Dynamic View?
^^^^^^^^^^^^^^^^^^^^^

In the type-specific views, BASIL focuses on one work item type at a time.
The user has to switch views to see how other work item types relate to the same specification.

This works well when concentrating on a specific type, but sometimes a broader picture is needed:

+ Which sections of the specification are covered by **any** work item, regardless of type?
+ Which sections are still completely uncovered?
+ How do all the different work item types relate to the same section of the document?

The Dynamic View answers these questions in a single screen.


Layout
^^^^^^

The Dynamic View is a two-column table:

+ **REFERENCE DOCUMENT** (left column): The full specification text. Sections covered by at least one work item are highlighted in green with a left border. Uncovered sections appear in a lighter color.
+ **WORK ITEMS** (right column): All directly mapped work items organized by type (Software Requirements, Test Specifications, Test Cases, Justifications, Documents). Each work item is shown as a card with its ID, version, status, coverage, and a summary of its content.


Selecting a work item
^^^^^^^^^^^^^^^^^^^^^

Clicking on any work item card in the right column selects it.
When selected:

+ The card is visually highlighted.
+ The reference document column updates to show only the portions of the specification that are mapped to the selected work item.
+ The page scrolls to the top so that both the relevant specification text and the selected card are visible.

To deselect, click the same card again or click the **Show full document** button that appears above the reference document.


Nested traceability
^^^^^^^^^^^^^^^^^^^

For Software Requirements that have children (nested Software Requirements, Test Specifications, or Test Cases) and for Documents that have nested Documents, the Dynamic View shows them inline under the parent work item card.
The **Indirect Test Specification** and **Indirect Test Case** switches at the top of the Mapping page also apply to the Dynamic View.
When enabled, indirect children appear indented below the parent work item card with a migration icon to distinguish them from direct mappings.


Snippet management
^^^^^^^^^^^^^^^^^^

Each work item card in the Dynamic View shows a badge indicating the number of specification snippets mapped to it.
A single work item can be mapped to multiple sections of the specification through different snippets.
Logged-in users with write permissions can click the **Manage Snippets** button on each card to open the snippets modal where they can:

+ View all snippet mappings for that work item.
+ Add new snippet mappings to relate the work item to additional sections of the specification.
+ Edit existing snippet sections, offsets, and coverage values.
+ Remove snippet mappings that are no longer needed.


Context menu
^^^^^^^^^^^^

Each work item card in the Dynamic View includes a kebab menu (three dots icon) that provides access to the same actions available in the type-specific views: editing the work item, viewing details, checking history, usage analysis, forking, deleting, and adding comments.
For Software Requirements, the menu also allows creating nested Test Specifications and Test Cases.
For Test Specifications, the menu allows creating nested Test Cases.
