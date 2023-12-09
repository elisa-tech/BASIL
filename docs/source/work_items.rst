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

Possible Children Work Item Types:

+ None

--------------------
Software Requirement
--------------------
Describe what the Software Component should do.

Default Fields:

+ title
+ description

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

Possible Children Work Item Types:

+ None
