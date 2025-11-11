.. image:: ../../app/src/app/bgimages/basil_black.svg

Work Items
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:


-------------
Justification
-------------
Often used to highlight the reason why a section of the Specification Document can't be related to any other work item type.

Default Fields:

+ description
+ status

Possible Children Work Item Types:

+ None

--------
Document
--------
Document is a general purpose work item that allow users to specify all relationships supported by SPDX.
BASIL distinguishes between text files and other files.
In case of text files, user can specify also a snippet of the document.
Moreover in that case BASIL automatically validate the relationships checking that the selected section still exists at the target offset.
This way user can be notified in case of changes.

Default Fields:

+ title
+ description
+ document_type (file or text)
+ status
+ spdx_relation
+ url
+ section (only in case of text file)
+ offset (only in case of text file)

Possible Children Work Item Types:

+ Document

--------------------
Software Requirement
--------------------
Describe what the Software Component should do.

Default Fields:

+ title
+ description
+ status

Possible Children Work Item Types:

+ Sw Requirement
+ Test Specification
+ Test Case

------------------
Test Specification
------------------
Is a description of a Test procedure. Doesn't refer to a specific implementation.
We can have different implementation (written also in different programming languages) that refers to a Test Specification.
It can be used as requirement for test case development and can be useful to track what remain to be implemented.

Default Fields:

+ title
+ preconditions
+ test_description
+ expected_behavior
+ status

Possible Children Work Item Types:

+ Test Case

---------
Test Case
---------
It is the implementation of a test procedure.

Default Fields:

+ title
+ description
+ repository
+ relative_path
+ status

Possible Children Work Item Types:

+ None

----------------
Work Item Status
----------------
BASIL support following status for above mentioned work items:

+ NEW
+ IN PROGRESS
+ IN REVIEW
+ REJECTED
+ REWORK
+ APPROVED

Example of typical workflows can be:

NEW --> IN PROGRESS --> IN REVIEW --> APPROVED

NEW --> IN PROGRESS --> IN REVIEW --> REJECTED --> REWORK --> IN REVIEW --> APPROVED
