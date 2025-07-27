Unreleased
----------

Enhancements:

* Add support for the Workgroup API.

* Account services (kerberos, seas, et al) all have a status.  Previously,
  the only visibility into status was via ``is_active``.  Now, the ``status``
  property gives you the exact status (it's an Enum), with possible statuses
  "active", "inactive", and "frozen".  ``is_active`` is still a property, and
  returns ``True`` iff the status is "active" (else it returns ``False``).

Fixed:

* Although the project is fully typed, the PEP 561 marker file was missing (`#2`_).

* A number of Account services properties had incorrect types.

Other:

* Bandit and CodeQL checks are being performed on all pushes and pull requests.

* The docs on Read the Docs were not building properly.

0.50.1
------

Do a release that will hopefully actually push to prod!

0.50.0
------

First alpha version!

Includes support for the base client (MAISClient), and the Accounts API.

.. _#2: https://github.com/stanford-rc/mais-apis-python/issues/2
