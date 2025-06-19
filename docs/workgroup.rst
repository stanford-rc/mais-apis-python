=============
Workgroup API
=============

This is the documentation for the Python client for the MaIS Workgroup API.
Everything you need is available in the :mod:`stanford.mais.workgroup.workgroup`
module.

To begin using the MaIS Workgroup API, you should first instantiate a
:class:`~stanford.mais.client.MAISClient` object.  Once that is done, you can
use it to instantiate an :class:`~stanford.mais.workgroup.WorkgroupClient`
object.

.. _Workgroup API Client:

Workgroup API Client
====================

You will use the :class:`~stanford.mais.workgroup.WorkgroupClient` instance to
access the API.  Once that is done, there are several ways you can access
workgroups (which will be instances of the :meth:`~stanford.mais.workgroup.Workgroup`
class).

One way is to use the :meth:`~stanford.mais.workgroup.WorkgroupClient.get`
method to fetch a workgroup.  The client instance provides mapping support, so
you can also use these methods to fetch a workgroup:

.. code-block:: python

    wclient = WorkgroupClient(...)

    # These two operations give you the same Workgroup:
    nero_users = wclient.get('nero:users')
    nero_users = wclient['nero:users']

If you want to search for workgroups, you can search for workgroups by name.
Search results do not include all the details of the workgroups, so if you want
full information, you need to make a call to fetch the full details of the
workgroup:

.. code-block:: python

    wclient = WorkgroupClient(...)
    nero_workgroup_results = wclient.search_by_name('nero:*')
    nero_workgroups = list(result.workgroup() for result in nero_workgroup_results)

The search results—in the form of instances of class
:class:`~stanford.mais.workgroup.PartialWorkgroup` — include the workgroup
name and description, which might be enough for you:

.. code-block:: python

    wclient = WorkgroupClient(...)
    nero_workgroup_results = wclient.search_by_name('nero:*')
    print("The nero stem has " + len(nero_workgroup_results) + " workgroups:")
    for nero_workgroup in nero_workgroup_results:
        print(f"    {nero_workgroup.name}: {nero_workgroup.description}")

.. autoclass:: stanford.mais.workgroup.WorkgroupClient
   :members:

.. autoclass:: stanford.mais.workgroup.PartialWorkgroup
   :members:

Workgroup
=========

You use a :class:`~stanford.mais.workgroup.Workgroup` instance to interact with
your workgroup.

Workgroup Fetch, Create, & Refresh
==================================

The :class:`~stanford.mais.workgroup.WorkgroupClient` can be used to fetch and
create workgroups, but :class:`~stanford.mais.workgroup.Workgroup` also
provides classmethods to do the same:

.. code-block:: python

   wclient = WorkgroupClient(...)

   # These three operations give you the same Workgroup:
   nero_users = wclient.get('nero:users')
   nero_users = wclient['nero:users']
   nero_users = Workgroup.get(client=wclient, name='nero:users')

Once a :class:`~stanford.mais.workgroup.Workgroup` instance has been created
(through :meth:`~stanford.mais.workgroup.Workgroup.get`,
:meth:`~stanford.mais.workgroup.Workgroup.create`, etc.), any attempts to
:meth:`~stanford.mais.workgroup.Workgroup.get` the same workgroup will return
an instance from the cache.  So, to update the data in your instance, run the
:meth:`~stanford.mais.workgroup.Workgroup.refresh` method.

.. automethod:: stanford.mais.workgroup.Workgroup.create

.. automethod:: stanford.mais.workgroup.Workgroup.get

.. automethod:: stanford.mais.workgroup.Workgroup.refresh

Workgroup Properties
====================

.. autoclass:: stanford.mais.workgroup.Workgroup

Read-only Properties
--------------------

Four (read-only) properties can be read even if the workgroup has been deleted:

.. autoproperty:: stanford.mais.workgroup.Workgroup.client
.. autoproperty:: stanford.mais.workgroup.Workgroup.name
.. autoproperty:: stanford.mais.workgroup.Workgroup.last_refresh
.. autoproperty:: stanford.mais.workgroup.Workgroup.deleted

Two properties are read-only, and can only be read if the workgroup is not
deleted:

.. autoproperty:: stanford.mais.workgroup.Workgroup.last_update
.. autoproperty:: stanford.mais.workgroup.Workgroup.can_see_membership

Read-write Properties
---------------------

These properties are **read-write**, and can only be read if the workgroup is
not deleted:

.. warning::
    These properties may only be changed if your client certificate is an
    administrator of the workgroup, either directly or via stem ownership.

.. autoproperty:: stanford.mais.workgroup.Workgroup.description
.. autoproperty:: stanford.mais.workgroup.Workgroup.privgroup
.. autoproperty:: stanford.mais.workgroup.Workgroup.reusable
.. autoproperty:: stanford.mais.workgroup.Workgroup.visibility
.. autoclass:: stanford.mais.workgroup.properties.WorkgroupVisibility
   :members:
.. autoproperty:: stanford.mais.workgroup.Workgroup.filter
.. autoclass:: stanford.mais.workgroup.properties.WorkgroupFilter
   :members:

Workgroup Membership
====================

Within your :class:`~stanford.mais.workgroup.Workgroup` instance, you can
access (and modify) the workgroup's members and administrators using the
:attr:`~stanford.mais.workgroup.Workgroup.members` and
:attr:`~stanford.mais.workgroup.Workgroup.administrators` properties.

.. autoproperty:: stanford.mais.workgroup.Workgroup.members
.. autoproperty:: stanford.mais.workgroup.Workgroup.administrators

.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembership
.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipPersonContainer
.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipWorkgroupContainer
.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipCertificateContainer
