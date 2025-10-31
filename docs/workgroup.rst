=============
Workgroup API
=============

This is the documentation for the Python client for the MaIS Workgroup API.
Everything you need is available here.

To begin using the MaIS Workgroup API, you should first instantiate a
:class:`~stanford.mais.client.MAISClient`.  Once that is done, you can
use it to instantiate a :class:`~stanford.mais.workgroup.WorkgroupClient`.

.. _Workgroup API Client:

********************
Workgroup API Client
********************

You will use the :class:`~stanford.mais.workgroup.WorkgroupClient` instance to
access the Workgroup API.  Instantiating a
:class:`~stanford.mais.workgroup.WorkgroupClient` is easy:

.. code-block:: python

    client = MAISClient(...)
    wclient = WorkgroupClient(client)

For performance, the :class:`~stanford.mais.workgroup.WorkgroupClient`
maintains a cache of fetched workgroups.  To clear the cache, call
:meth:`~stanford.mais.workgroup.WorkgroupClient.clear_cache`.

.. warning::
   Once you clear the cache, avoid using any Workgroup instances that you might
   have used before!

Fetching Workgroups
===================

Once you have a :class:`~stanford.mais.workgroup.WorkgroupClient`, there are
several ways you can access workgroups.  The workgroups you access will be
instances of the :class:`~stanford.mais.workgroup.Workgroup` class.

One way is to use the :meth:`~stanford.mais.workgroup.WorkgroupClient.get`
method to fetch a workgroup, providing the name of the workgroup that you want.

.. important::
   Workgroup names are all lowercase.

The
:class:`~stanford.mais.workgroup.WorkgroupClient` also implements the
`__getitem__` method, so instead of calling
:meth:`~stanford.mais.workgroup.WorkgroupClient.get` you can get workgroups as
you would items from a dict.

Here is an example of the two ways you can get a workgroup.

.. code-block:: python

    wclient = WorkgroupClient(...)

    # These two operations give you the same Workgroup:
    nero_users = wclient.get('nero:users')
    nero_users = wclient['nero:users']

Searching for Workgroups
========================

Workgroup Existence 
-------------------

If you know the name of the workgroup you are looking for, the
:class:`~stanford.mais.workgroup.WorkgroupClient` implements
:class:`~collections.abc.Container` functionality, so you can use the client to
check if a workgroup exists:

.. code-block:: python

    wclient = WorkgroupClient(...)
    nero_admins = (wclient['nero:admins'] if 'nero:admins' in wclient else None)

Searching by Name
-----------------

Workgroups can be searched for by using a "starts with" -style search with
wildcards.  Search results do not include all the details of the workgroups, so
if you want full information, you need to make a call to fetch the full details
of the workgroup:

.. code-block:: python

    wclient = WorkgroupClient(...)
    nero_workgroup_results = wclient.search_by_name('nero:*')
    nero_workgroups = list(result.workgroup() for result in nero_workgroup_results)

.. important::
   You must have at least four characters in your search string, before your
   first wildcard.  Searching for ``abc:*`` will work, but if you search for
   ``ab:*``, you'll get an IndexError.

Although it's common to put a single asterisk at the end of the search—for a
"starts with" type of search—you can put wildcards in the middle of a search:

.. code-block:: python

    wclient = WorkgroupClient(...)
    owner_workgroup_results = wclient.search_by_name('workgroup:*-owners')
    owner_workgroups = list(result.workgroup() for result in owner_workgroup_results)

The search results — instances of class
:class:`~stanford.mais.workgroup.PartialWorkgroup` — include the workgroup
name and description, which might be enough for you:

.. code-block:: python

    wclient = WorkgroupClient(...)
    nero_workgroup_results = wclient.search_by_name('nero:*')
    print("The nero stem has " + len(nero_workgroup_results) + " workgroups:")
    for nero_workgroup in nero_workgroup_results:
        print(f"    {nero_workgroup.name}: {nero_workgroup.description}")

Searching by Membership
-----------------------

Besides searching for workgroups by name, you can also search for workgroups
based on who (or what) is included in a workgroup.
:meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_user` searches for
workgroups by SUNetID, returning workgroups containing the user as a direct
**or indirect** member or administrator.  

.. important::
   This search may give unexpected results!

For example, say a user is a member of workgroup `test:a`, and `test:a` is
nested into the administrators of `test:b`.  Here is what you would see when
running a search:

.. code-block:: python

    wclient = WorkgroupClient(...)
    results = wclient.search_by_user('user')
    a_in_results = any(wg.name == 'test:a' for wg in s.is_member) # True
    b_in_results = any(wg.name == 'test:b' for wg in s.is_administrator) # Also True!

If you want to want to check if the user is directly in the workgroup, you have
to look up the workgroup and check.  For example:

.. code-block:: python

    wclient = WorkgroupClient(...)
    results = wclient.search_by_user('user')
    b_in_results = any(wg.name == 'test:b' for wg in s.is_administrator) # True
    
    wg = wclient['test:b'] # Membership checks need the full workgroup
    user_in_b = ('user' in wg.administrators.people) # False!
    a_in_b = ('test:a' in wg.administrators.workgroups) # True!

    wga = wclient['test:a'] # Fetch test:a to check
    user_in_a = ('user' in wga.members.people) # True!

In the above example, `user` is an administrator of `test:b`, but only because
`user` is a member of `test:a`, and all members of `test:a` are administrators
of `test:b`.

In addition to searching for workgroups containing a person, you can search for
workgroups containing a workgroup (using
:meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_workgroup`), and you
can search for workgroups containing a certificate (using
:meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_certificate`).  The
behavior of
:meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_workgroup` and
:meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_certificate` is the
same as :meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_user`.

.. note::
   :meth:`~stanford.mais.workgroup.WorkgroupClient.search_by_workgroup` is
   special: In addition to accepting a workgroup name as a string, you can
   provide a :class:`~stanford.mais.workgroup.Workgroup` or
   :class:`~stanford.mais.workgroup.PartialWorkgroup` as the search parameter,
   and the name will be extracted.

Creating Workgroups
===================

Creating workgroups can be done by calling
:meth:`~stanford.mais.workgroup.WorkgroupClient.create`.  The only required
parameters are a name and description.

.. code-block:: python

    wclient = WorkgroupClient(...)
    wg = wclient.create('test:a', 'My Test Workgroup')

When you only provide required parameters to
:meth:`~stanford.mais.workgroup.WorkgroupClient.create`, the following defaults
are used:

* :attr:`~stanford.mais.workgroup.Workgroup.filter`: none

* :attr:`~stanford.mais.workgroup.Workgroup.privgroup`: enabled

* :attr:`~stanford.mais.workgroup.Workgroup.reusable`: yes

* :attr:`~stanford.mais.workgroup.Workgroup.visibility`: Stanford

If you want to change these, you may do so changing the properties of the
created workgroup instance, or you can provide them during creation, like so:

.. code-block:: python

    wclient = WorkgroupClient(...)
    wg = wclient.create(
        name='test:a',
        description='My Test Workgroup',
        filter=WorkgroupFilter.ACADEMIC_ADMINISTRATIVE,
        privgroup=True,
        reusable=True,
        visibility=WorkgroupVisibility.PRIVATE
    )

.. note::
   Members and administrators can only be added after the workgroup is created.

Your newly-created workgroup will not have any members, but it will have two
administrators:

* The stem-owner workgroup will be an administrator.  For example, workgroup
  `test:a` will have `workgroup:test-owners` as an administrator.  This cannot
  be changed or removed.

* The certificate which created the workgroup will be an administrator.  This
  *can* be removed.

***************
Workgroup Class
***************

You use a :class:`~stanford.mais.workgroup.Workgroup` instance to interact with
your workgroup.

Fetch, Create, Refresh, & Delete
================================

The :class:`~stanford.mais.workgroup.WorkgroupClient` can be used to fetch and
create workgroups, but :class:`~stanford.mais.workgroup.Workgroup` also
provides classmethods to do the same:

.. code-block:: python

   wclient = WorkgroupClient(...)

   # These three operations give you the same Workgroup:
   nero_users = wclient.get('nero:users')
   nero_users = wclient['nero:users']
   nero_users = Workgroup.get(client=wclient, name='nero:users')

   # You can also use a classmethod to create a workgroup:
   Workgroup.create(
     client=wclient,
     name='nero:sysadmins',
     description='Nero sysadmins',
   )

Once a :class:`~stanford.mais.workgroup.Workgroup` instance has been created
(through :meth:`~stanford.mais.workgroup.Workgroup.get`,
:meth:`~stanford.mais.workgroup.Workgroup.create`, etc.), any attempts to
:meth:`~stanford.mais.workgroup.Workgroup.get` the same workgroup will return
an instance from the cache.  So, to update the data in your instance, run the
:meth:`~stanford.mais.workgroup.Workgroup.refresh` method.

.. important::
   Once you call :meth:`~stanford.mais.workgroup.Workgroup.refresh`, you must
   be prepared for *anything* to change (except the workgroup name).  It's even
   possible for the workgroup to be deleted!

As for deleting a workgroup, that is accomplished using the
:meth:`~stanford.mais.workgroup.Workgroup.delete` method.

.. code-block:: python

   wclient = WorkgroupClient(...)
   nero_users = wclient.get('nero:users')
   nero_users.delete()

Deleting a workgroup is immediate, but not permanent: Deleted workgroups are
simply made 'inactive'.  Should you every try fetching or modifying a deleted
workgroup, a :class:`~stanford.mais.workgroup.WorkgroupDeleted` exception will
be raised.

Deleted workgroups may be un-deleted by a stem owner, through the Workgroup
Manager web site.

Properties
==========

Every :class:`~stanford.mais.workgroup.Workgroup` has properties, some of which
are read-only and some of which may be modified (assuming you have
permissions).

.. note::
   This section provides summaries only.  See the Module Documentation for
   details about each property!

Read-only Properties
--------------------

Four (read-only) properties can be read even if the workgroup has been deleted:

* :attr:`~stanford.mais.workgroup.Workgroup.name`: The workgroup's name.

* :attr:`~stanford.mais.workgroup.Workgroup.deleted`: True if the workgroup has
  been deleted; False otherwise.

* :attr:`~stanford.mais.workgroup.Workgroup.client`: This returns the
  :class:`~stanford.mais.workgroup.WorkgroupClient` which was used to fetch the
  workgroup.

* :attr:`~stanford.mais.workgroup.Workgroup.last_refresh`: This is the last
  time that the *full* workgroup was fetched from the API, which happens when
  calling :meth:`~stanford.mais.workgroup.Workgroup.refresh` or when changing
  one of the properties.

  .. important::
     Changing a workgroup's members or administrators does *not* trigger a
     refresh.

Two properties are read-only, and can only be read if the workgroup is not
deleted:

* :attr:`~stanford.mais.workgroup.Workgroup.last_update`: The
  :class:`datetime.date` when the workgroup (not the
  :class:`~stanford.mais.workgroup.Workgroup` instance, the actual underlying
  workgroup) was last changed.

  .. warning::
     This date is in the Stanford-local time zone.  Remember to take
     this into account when doing comparisons.

* :attr:`~stanford.mais.workgroup.Workgroup.can_see_membership`: True if your
  client certificate is able to see a workgroup's membership; False otherwise.

Read-write Properties
---------------------

These properties are **read-write**, and can only be read if the workgroup is
not deleted.

.. warning::
    These properties may only be changed if your client certificate is an
    administrator of the workgroup, either directly or via stem ownership.

* :attr:`~stanford.mais.workgroup.Workgroup.description`: The workgroup's
  description, limited to 255 Latin1-encoded characters.

* :attr:`~stanford.mais.workgroup.Workgroup.filter`: The affiliations of people
  who are allowed to be members of the workgroup.

* :attr:`~stanford.mais.workgroup.Workgroup.privgroup`: True if this
  workgroup has a privgroup.

* :attr:`~stanford.mais.workgroup.Workgroup.reusable`: True if this workgroup
  may be nested into workgroups outside the same stem.  (Workgroups may always
  be nested within the same stem.)

* :attr:`~stanford.mais.workgroup.Workgroup.visibility`: The visibility of this
  workgroup's members and administrators.

********************
Workgroup Membership
********************

Within your :class:`~stanford.mais.workgroup.Workgroup` instance, you can
access (and modify) the workgroup's members and administrators using the
:attr:`~stanford.mais.workgroup.Workgroup.members` and
:attr:`~stanford.mais.workgroup.Workgroup.administrators` properties.

.. note::
   :attr:`~stanford.mais.workgroup.Workgroup.members` and
   :attr:`~stanford.mais.workgroup.Workgroup.administrators` are almost
   identical in how they work, so this guide will focus on
   :attr:`~stanford.mais.workgroup.Workgroup.members` only.  When there is a
   behavior difference between
   :attr:`~stanford.mais.workgroup.Workgroup.members` and
   :attr:`~stanford.mais.workgroup.Workgroup.administrators`, the difference
   will be mentioned.

.. warning::
   The :attr:`~stanford.mais.workgroup.Workgroup.members` and
   :attr:`~stanford.mais.workgroup.Workgroup.administrators` properties should
   only be retained for a short amount of time.  They are closely tied to their
   associated :class:`~stanford.mais.workgroup.Workgroup`.

To get the total number of members, use ``len``:

.. code-block:: python

   wclient = WorkgroupClient(...)

   nero_users = wclient.get('nero:users')

   number_of_members = len(nero_users.members)

   number_of_members == (
     len(nero_users.members.people) +
     len(nero_users.members.workgroups) +
     len(nero_users.members.certificates)
   ) # True

When you access a workgroup's membership through
:attr:`~stanford.mais.workgroup.Workgroup.members`, you will receive an
instance which has three properties:

* :attr:`~stanford.mais.workgroup.member.WorkgroupMembership.people`: The
  people who are members of the workgroup.  Each set member is a SUNetID.

* :attr:`~stanford.mais.workgroup.member.WorkgroupMembership.workgroups`: The
  nested workgroups.  Each set member is a workgroup name.

* :attr:`~stanford.mais.workgroup.member.WorkgroupMembership.certificates`: The
  certificates who are members of the workgroup.  Each set member is a
  certificate CN (Common Name).

  .. note::
    In almost all cases, certificates may only be administrators of workgroups,
    not members.  The exception is that certificates may be stem owners, so they
    *are* allowed to be members of stem-owner ``workgroup:*-owners`` workgroups.

:attr:`~stanford.mais.workgroup.member.WorkgroupMembership.people`,
:attr:`~stanford.mais.workgroup.member.WorkgroupMembership.workgroups`, and
:attr:`~stanford.mais.workgroup.member.WorkgroupMembership.certificates` are
all sets of strings: You may get the set's length, iterate over the sets
members, add set members, remove set members, etc..  Each set will raise an
exception if you attempt to add an inappropriate type of string (for example,
attempting to add a workgroup to
:attr:`~stanford.mais.workgroup.member.WorkgroupMembership.people`).

Here is an example of how to remove a person from membership of all workgroups
in a stem:

.. code-block:: python

   wclient = WorkgroupClient(...)
   person_to_remove = 'jsmith'

   test_workgroup_results = wclient.search_by_name('test:*')
   for test_workgroup_result in test_workgroup_results:
     test_workgroup = test_workgroup_result.workgroup()
     test_workgroup.members.people.discard(person_to_remove)

Since the :meth:`~frozenset.discard` method only removes from the set if the
element is in the set (in other words, it ignores :class:`KeyError`), we do not
need to check for set membership first.

.. warning::
   This is a simplified example, which skips all error checking.  Be sure to
   read the Module Documentation before using this code for production work!

*********
Privgroup
*********

A workgroup's membership is a collection of people, workgroups, and
certificates, but downstream systems are normally only able to think in terms
of people: Downstream systems don't care if a person is a member of
`workgroup:x` directly or indirectly, they just care if a person is a member.
So, downstream systems do not normally think about workgroups, they think about
*privgroups*.

A privgroup is a list of SUNetIDs. A workgroup has two privgroups: One for
members and one for administrators.  You can fetch both lists by calling
:meth:`~stanford.mais.workgroup.Workgroup.get_privgroup`.

For example, you can use
:meth:`~stanford.mais.workgroup.Workgroup.get_privgroup` to get the names of
everyone who is a member of a workgroup:

.. code-block:: python

   wclient = WorkgroupClient(...)
   nero_users_workgroup = wclient.search_by_name('nero:users')
   nero_users_privgroup = nero_users_workgroup.get_privgroup()

   with open('nero_usernames.txt', mode='w', encoding='ascii') as f:
     for nero_user in nero_users_privgroup.members:
       print(nero_user.sunetid, file=f)

:meth:`~stanford.mais.workgroup.Workgroup.get_privgroup` is the better option
for this case, because ``nero_users_workgroup.members.people`` would only
return people who are *direct* members of the workgroup.  Indirect
members—people who are members because they are members of a nested
workgroup—are not included in ``nero_users_workgroup.members.people``.

A workgroup only has a privgroup if the workgroup's
:attr:`~stanford.mais.workgroup.Workgroup.privgroup` property is True.
Privgroups are created by starting with all of the members (or administrators)
who are people.  If a workgroup is nested, then the nested workgroup's
privgroup is calculated and included.  Finally, filters are applied.  When
constructing a privgroup, all certificates are ignored.

.. note::
   The Workgroup Manager web site only makes privgroup listings available
   to workgroup administrators.  The API, however, allows all client
   certificates to get the privgroup of all stanford-visible workgroups, and
   all workgroups where the client certificate is an administrator.

.. important::
   The steps for generating a privgroup listing is complicated.  For details,
   see the Module Documentation of
   :meth:`~stanford.mais.workgroup.Workgroup.get_privgroup`.

********************
Module Documentation
********************

Here is detailed documentation for all Workgroup modules.

stanford.mais.workgroup
=======================

:class:`~stanford.mais.workgroup.WorkgroupClient` represents your Workgroup API
client.

.. autoclass:: stanford.mais.workgroup.WorkgroupClient
   :members:

Searches for workgroups never return full
:class:`~stanford.mais.workgroup.Workgroup` instances, they return
:class:`~stanford.mais.workgroup.PartialWorkgroup` instances.

.. autoclass:: stanford.mais.workgroup.PartialWorkgroup
   :members:

When doing a "search by" -type search, the results are separated into "search
target is an administrator" and "search target is a member".  The actual return
type is :class:`~stanford.mais.workgroup.SearchByResults`.

.. autoclass:: stanford.mais.workgroup.SearchByResults
   :members:


stanford.mais.workgroup.workgroup
=================================

This module defines our :class:`~stanford.mais.workgroup.Workgroup` class, and
some related classes.

.. autoclass:: stanford.mais.workgroup.Workgroup
   :members:

When fetching a workgroup's privgroup, the return type is a
:class:`~stanford.mais.workgroup.PrivgroupContents`, with properties for
accessing a privgroup's members and a privgroup's administrators.

.. autoclass:: stanford.mais.workgroup.PrivgroupContents
   :members:

Each property is a :class:`~stanford.mais.workgroup.PrivgroupEntry`.

.. autoclass:: stanford.mais.workgroup.PrivgroupEntry
   :members:

Finally, :class:`~stanford.mais.workgroup.workgroup.WorkgroupDeleted` is an
exception which will be raised when trying to access or change a workgroup that
has been deleted.

.. autoclass:: stanford.mais.workgroup.WorkgroupDeleted
   :show-inheritance:
   :members:

stanford.mais.workgroup.properties
==================================

There are two :class:`~stanford.mais.workgroup.Workgroup` properties which are
not text fields or booleans.  Those two properties are represented as enums,
and are defined in this module.

:class:`~stanford.mais.workgroup.properties.WorkgroupFilter` is used to control
the effective membership of a workgroup.

.. autoclass:: stanford.mais.workgroup.properties.WorkgroupFilter
   :members:

:class:`~stanford.mais.workgroup.properties.WorkgroupVisibility` is used to
control who can see a workgroup's members & administrators.

.. autoclass:: stanford.mais.workgroup.properties.WorkgroupVisibility
   :members:

stanford.mais.workgroup.members
===============================

Every workgroup contains two collections of containers, one for members —
accessed through the :attr:`~stanford.mais.workgroup.Workgroup.members`
property — and one for administrators — accessed through the
:attr:`~stanford.mais.workgroup.Workgroup.administrators` property.  The
code implementing those collections exists in this module.

Each collection of containers is an instance of
:class:`~stanford.mais.workgroup.member.WorkgroupMembership`.

.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembership
   :members:

Each collection has three containers: One container of people, one container of
workgroups, and one container of certificates.  The base class for containers
is :class:`~stanford.mais.workgroup.member.WorkgroupMembershipContainer`.

.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipContainer
   :members: add, discard

The container of people is represented by the
:class:`~stanford.mais.workgroup.member.WorkgroupMembershipPersonContainer`.

.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipPersonContainer

The container of workgroups is represented by the
:class:`~stanford.mais.workgroup.member.WorkgroupMembershipWorkgroupContainer`.

.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipWorkgroupContainer

The container of certificates is represented by the
:class:`~stanford.mais.workgroup.member.WorkgroupMembershipCertificateContainer`.

.. autoclass:: stanford.mais.workgroup.member.WorkgroupMembershipCertificateContainer
