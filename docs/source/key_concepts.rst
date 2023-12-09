.. image:: ../../app/src/app/bgimages/basil_black.svg

Key Concepts
============



------------------
Reference Document
------------------

With BASIL it is possible to create work items and justifications against any plain text file that we can call generically Reference Document.
BASIL will follow any changes to the Reference Document and that will affect the relationship to the work items.
Usually the Reference Document, as a plain text file, it is stored in a git repository.
To keep track of all the version of the Reference Document in BASIL, a user can define multiple versions of a Software Component and relate to each version a specific commit of the Reference Document.
Using a specific commit, each version will be fixed and the relationships defined to the work items will persists.
So this way the changes to the Reference Document are not affecting the relationships.
If we want to setup BASIL in a way that any changes to the Reference Document will affect work item relationships, we can have just one Software Component version that is connected to the head of the git repository where the Reference Document is stored.


-----------------
Re-Use Work Items
-----------------

Once defined a work item, working with a particular Software Component, a user can re use the same work item to a different Software Component or to create a relationship with another piece of the Reference Document in the same Software Component.
With that said, we can think on different scenarios.
For example, a project that want to store Software Requirements in text file inside a git repository can create a sort of requirements database in BASIL.
That will help on keeping track of any changes to the Software Requirements files and in the meantime we can reuse those Software Requirement creating relationship to other software components.


----------------
Fork a Work Item
----------------

Imagine that we have a Software Requirement used across several Software Components and for any reason we need to change it only for a particular Software Component.
It will be possible, forking the Software Requirement in that Software Component relationship.
That will create a new Software Requirement, with a new ID (you can check it from history).
So any changes to that new Software Requirement will affect it only and not the other instances scattered across Software Components because now they are two different work items.


--------------
Usage Analysis
--------------

BASIL provide a feature to check where a work items is used.
So, from the context menu related to each work items, the Usage button will provide a list of all Software Components that are using it.
That is aimed to help on understanding the effect of any changes to the work items.
That because you will know that changes will affect also other work items and in that case you would like (or not) to fork it before editing.


-------
History
-------

BASIL provide a feature to check a work item history.
As in BASIL work items live in combination with a section of the target document, the version is itself a combination of two numbers eg.: 2.3.
The first number refer to the work item version, so it will take in consideration all the changes applied to the work item fields.
The second number, instead, refer to the relationship version. That because the relationship holds some information like the offset, section and coverage.
So, the second number in the version will take care about any changes to those information.
Using the context menu related to each work items, and clicking the **History** button you will be able to see all the fields modified on each version.


-------------
Mapping Views
-------------

BASIL provides different mapping views. A user can select the desired view from the Mapping page using the combo box in the top section of the page.
You will see a value for each work item types and an additional view named Raw Specification.
The key concept is that selecting a particular view from that combo box you will focus on Work items with direct mapping to the Software Specification Document (or Source Code).
A user can create a direct mapping of a Test Case against a section of the Specification and to be able to see it a user have to select the **Test Cases** view.
A user can have the same Test Case in the Software Requirements view if the Test Case is nested under a Software Requirement.
Why that is possible?
Because not all the companies/users want to create all those work items.
So if a user just want to create Test Cases and map them to sections of the specification document that will be possible.



.. toctree::
   :maxdepth: 1
   :caption: Contents:
