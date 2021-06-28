================================
Stanford MaIS APIs Python Client
================================

This is a Python client for interacting with Stanford MaIS APIs.

The `Middleware and Integration Services`_ group, part of `University IT`_,
provides many APIs for reading information from the _Registry_, the data store
that contains information about people, accounts, groups, courses, and more.
Although the data sets seem simple, come from many different sources (for
example, student records and HR records).

MaIS provides access to these data sets to authorized clients, through a set of
XML and JSON APIs.  This package provides a Python SDK for interfacing with
some of those APIs.

.. _Middleware and Integration Services: https://mais.stanford.edu/
.. _University IT: https://uit.stanford.edu/

Example
-------

Here is an example of how you can use the Accounts API through this SDK:

.. code::

   from stanford.mais.client import MAISClient
   from stanford.mais.account import AccountClient
   from pathlib import Path

   # Keep this secret!
   client_cert = Path('client.pem')

   # Set up clients
   client = MAISClient.prod(client_cert)  # You can also use .uat() for UAT.
   accounts = AccountClient(client)

   # Fetch an account
   lelandjr = accounts.get('lelandjr')  # This is one way, or …
   lelandjr = accounts['lelandjr']  # … you can do this!

   # Look at account information
   lelandjr.name  # "Stanford Jr., Leland
   lelandjr.services.library.is_active  # `True`

   # Only interested in accounts of people?
   sunetids = accounts.only_people()
   sunetids.get('shared-email')  # Raises KeyError

   # How about active people?
   active_sunetids = accounts.only_people().only_active()

   # Bulk validation of SUNetIDs
   list_of_ids = 'leland jane lelandjr asld-gkm'
   from stanford.mais.account.validate import validate
   validated_results = validate(list_of_ids)
   # validated_results.full={'jane'}
   # validated_results.base={'leland'}
   # validated_results.inactive={'lelandjr'}
   # validated_results.unknown={'asld-gkm'}

APIs Supported
--------------

The following APIs are supported:

* `Account`_: Full support for *Full Data* records for individual accounts,
  for both people (SUNetIDs) and functional account.  All of the information
  provided by the API is exposed, including service-specific settings.
  Support for 'views' that can act as if functional or inactive
  account don't exist (so you don't have to filter them out).

  *Not implemented*: Retrieving a list of accounts that changed status in
  the past X days.

Work is in progress on the following APIs:

* `Workgroup`_: Full support for operations on individual workgroups.
  Creating workgroups.  Modifying workgroup properties and membership.
  Fetching privilege groups.  Checking and making linkages.  Integration with
  the Accounts SDK (for workgroup membership).

  *Not currently planned*: Searching workgroups by an identifier (such as by
  part of a name, or by a member).  Deleting workgroups.

Support is not planned for the following APIs, as the author does not
currently have a need for them:

* `Course`_

* `Person`_

* `Privilege`_

* `Student`_

If you are interested in working on a full (or mostly-full) implementation for
an API, `reach out to us <mailto:srcc-support@stanford.edu>`_!

.. _Account: https://uit.stanford.edu/developers/apis/account
.. _Course: https://uit.stanford.edu/developers/apis/course
.. _Person: https://uit.stanford.edu/developers/apis/person
.. _Privilege: https://uit.stanford.edu/developers/apis/privilege
.. _Student: https://uit.stanford.edu/developers/apis/student
.. _Workgroup: https://uit.stanford.edu/developers/apis/workgroup2.0

Requirements
------------

* Python 3.9, or any later Python 3.x

  Older Python versions will be examined to see if they can be supported, but
  it is highly unlikely that Python 3.5 or older will be supported.  Python 2
  will not be supported.

* `Requests`_ 2.25.1, or any later 2.x

* A client certificate, issued by `MaIS`_, with permissions to the APIs you
  want to use, in the appropriate tier (such as PROD (production) or UAT).  See
  the `Getting Started`_ guide for more information.

* Testing requires `PyTest <https://docs.pytest.org/en/latest/>`_ and
  `requests-mock <https://requests-mock.readthedocs.io/>`_.

* Linting requires `MyPy <http://www.mypy-lang.org/>`_ and `types-requests
  <https://pypi.org/project/types-requests/>`_.

* Building documentation requires `Sphinx <http://www.sphinx-doc.org/>`_ and
  the `Sphinx RTD Theme <https://sphinx-rtd-theme.readthedocs.io>`_.

At this time, there is no explicit support for threads, multiple processes, or
async, though support may be added in the future.  Until then, you should be
safe to use these modules, so long as you don't share instances across
threads/packages.

.. _Requests: https://docs.python-requests.org/
.. _MaIS: https://mais.stanford.edu/
.. _Getting Started: https://uit.stanford.edu/developers/apis/getting-started

Copyright & Licensing
---------------------

The code and documentation is © The Board of Trustees of the Leland Stanford
Junior University.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, version 3.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see `<https://www.gnu.org/licenses/>`_.
