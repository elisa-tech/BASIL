.. image:: ../../app/src/app/bgimages/basil_black.svg

User Management
===============

You can navigate a BASIL instance without a BASIL user.
On doing so you will be recognized as a `guest` (not a GUEST as user role) and you will be able to navigate public contents.
You will not be able to leave comments, add or edit software components or work items.
You can create a BASIL user by your own navigating to the /signin page.
Creating a new user the default role will be GUEST.
An admin will be able to modify your role, to reset your password and to enable/disable your account.

-----
Roles
-----

BASIL support 3 different user roles: ADMIN, GUEST, USER.
 * ADMIN: same rules as USER but an ADMIN can also enable/disable other users and reset their password.
 * GUEST: Can navigate and add comments to public contents. A guest cannot create a new software components.
 * USER: Can navigate and add comments to public contents. Moreover a USER can work on Software Components accordingly with the user permission defined by owners/managers.


----------------
User Permissions
----------------

Creating a new Software Component a USER (or ADMIN) become its owner.
That allow the user the possibility to set other users permissions to this Software Component.

Here following the possible permissions and their meaning:

 * **Read** permission: Permission to read work items and relationships of the selected software component.
 * **Write** permission: Permission to add and edit work items and relationships of the selected software component.
 * **Edit** permission: Permission to edit informations of the selected software component.
 * **Owner** permission: Manage user permissions to the selected software component.

Note: It is not possible to assign Write, Edit and Owner permissions to a user with role GUEST.


----------------
Admin
----------------

An ADMIN can modify user roles, reset passwords and enable/disable other users from the User Management page.
Creating a BASIL instance, you can specify the BASIL_ADMIN_PASSWORD environment variable to setup the default admin credentials.


---------------
Public contents
---------------

As default a content is created as public.
As owner of a software component you can specify read permissions.
If you specify at least one user that cannot access a Software Component page, that will prevent also to any guest to reach it.


.. toctree::
   :maxdepth: 1
   :caption: Contents:
