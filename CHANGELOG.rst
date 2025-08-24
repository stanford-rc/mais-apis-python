0.51.1
------

Other:

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
