0.53.0
------

Enhancements:

* When changing a workgroup's property (such as its description), the Workgroup
  API returns a full workgroup record, as if we had also called ``refresh()``.
  We used to ignore that, but now we use it to update the Workgroup instance.
  This essentially means that every workgroup property change includes an
  implicit call to ``refresh()``.

  .. note::
      Changes to a workgroup's members or administrators will *not*
      trigger an implicit refresh.

* Calling ``Workgroup.refresh()`` on a deleted workgroup used to work silently,
  and clients were told to manually check if the ``Workgroup.deleted`` property
  changed.  Now, a ``WorkgroupDeleted`` exception is raised to make the
  deletion obvious.

* Any operation that makes an API call may now raise a `NotImplementedError`.
  This exception will be raised if the API returns an unexpected response code.

* Almost all tests have been added at this point.

Fixes:

* Until now, doing any actions (including ``get()``) on an already-deleted
  workgroup would have raised a ``ChildProcessError``.  This was because
  actions on already-deleted workgroups returned a 400 error, which we did not
  expect.  Now, we properly catch this situation, and return a new exception,
  ``WorkgroupDeleted``.

Other:

* When we discover that a workgroup has been deleted 'behind our back', in
  addition to raising a ``WorkgroupDeleted`` exception, the Workgroup instance
  is marked as deleted.

0.52.0
------

Enhancements:

* The Account "List of accounts that changed status in past x days" API
  operation is now supported.

* The Account service 'seas' has a new setting, ``emailservice``.

* When creating a new Workgroup, the ``privgroup`` setting now defaults to
  True, in line with the Workgroup API.

* When deleting a workgroup, the ``last_refreshed`` field now shows the
  datetime when the workgroup was deleted.

* More of the Workgroup code is tested.  Work is ongoing in this area.

Fixes:

* When creating a new Workgroup, the ``Workgroup.create()`` call was not
  including the ``privgroup`` and ``reusable`` properties in the API call.  All
  workgroups created by the ``create()`` call had the ``privgroup`` and
  ``reusable`` properties set to True.

* The WorkgroupClient's caching functionality was not fully-implemented.  Only
  calls to ``WorkgroupClient.get()`` were being cached.

Other:

* When doing ``from stanford.mais.workgroup import *``, you now get all of the
  names that come from running ``from stanford.mais.workgroup.workgroup import
  *`` That is, running ``from stanford.mais.workgroup import *`` now gets you
  ``WorkgroupFilter``, ``WorkgroupVisibility``, ``PrivgroupContents``, and
  ``PrivgroupEntry``.

* Fix a GitHub Actions problem preventing a single Git operation from releasing
  on both PyPi and Test PyPi in a single action (that is, in a single tag).

0.51.0
------

Enhancements:

* Account services (kerberos, seas, et al) all have a status.  Previously,
  the only visibility into status was via ``is_active``.  Now, the ``status``
  property gives you the exact status (it's an Enum), with possible statuses
  "active", "inactive", and "frozen".  ``is_active`` is still a property, and
  returns ``True`` iff the status is "active" (else it returns ``False``).

* In addition to ``is_active``, account services now has ``not_inactive``.

* All of the Account code is now fully tested.  From this point on, changes to
  the existing account SDK's structure is unlikely.

* Add support for the Workgroup API.  This doesn't have tests yet, and may
  still change, so it's not a top-line enhancement.

Fixed:

* Although the project is fully typed, the PEP 561 marker file was missing (`#2`_).

* A number of Account services properties had incorrect types.  Indeed, types
  have been cleaned up *a lot* in this release.

* Setting timeouts works properly!  Before now, not all operations honored the
  ``default_timeout`` that you might have set when you created your MAISClient.
  The ``default_timeout`` property, has changed, and is now simply the
  ``timeout`` property.

Other:

* In the Account class, the property ``last_updated`` is now ``last_update``.

* As of May 2025, the `autoreply service is no longer in use`_.  You should
  stop using the ``Account.service.autoreply`` property.

* Custom session support has gone through major changes!  Instead of providing
  a custom Requests Session to each service's constructor (AccountClient,
  WorkgroupClient, etc.), you now provide the custom Session to the
  ``MAISClient``'s constructor, using the ``session`` argument.

* Bandit and CodeQL checks are being performed on all pushes and pull requests.
  Coverage reports are also being generated for runs.  Nothing's being done
  with it, though.

* The docs on Read the Docs are now building properly.

* ``py.typed`` files are now provided, for type-checking support.  Also, more
  things (like tuples and dicts) have typing information provided.

0.50.1
------

Do a release that will hopefully actually push to prod!

0.50.0
------

First alpha version!

Includes support for the base client (MAISClient), and the Accounts API.

.. _#2: https://github.com/stanford-rc/mais-apis-python/issues/2

.. _autoreply service is no longer in use: https://uit.stanford.edu/news/stanford-accounts-getting-new-look
