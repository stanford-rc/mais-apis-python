================================
Stanford MaIS APIs Python Client
================================

.. image:: https://badge.fury.io/py/stanford-mais.svg
   :target: https://badge.fury.io/py/stanford-mais
   :alt: Badge showing the latest version available on PyPI
.. image:: https://img.shields.io/pypi/pyversions/stanford-mais?style=plastic
   :target: https://pypi.org/project/stanford-mais/
   :alt: Badge showing supported Python versions
.. image:: https://readthedocs.org/projects/mais-apis-python/badge/?version=latest
   :target: https://mais-apis-python.readthedocs.io/en/latest/?badge=latest
   :alt: Badge showing documentation build status

This is a Python client for interacting with Stanford MaIS APIs.

The `Middleware and Integration Services`_ group, part of `University IT`_,
provides many APIs for reading information from the `Registry`_, the data store
that contains information about people, accounts, groups, courses, and more.
Although the data stores seem simple, they come from many different sources (for
example, student records and HR records).

MaIS provides access to these APIs to authorized clients, through a set of
XML and JSON APIs.  This package provides a Python SDK for interfacing with
some of those APIs.

This package was created & is maintained by `Stanford Research Computing`_.  It
is made available to others in the hope that it will be useful!

.. _Middleware and Integration Services: https://mais.stanford.edu/
.. _University IT: https://uit.stanford.edu/
.. _Registry: https://uit.stanford.edu/service/registry
.. _Stanford Research Computing: https://srcc.stanford.edu

Example
-------

Here is an example of how you can use the Accounts API through this SDK:

.. code-block:: python

   from stanford.mais.client import MAISClient
   from stanford.mais.account import AccountClient
   from pathlib import Path

   # Keep this secret!
   client_cert = Path('client.pem')

   # Set up clients
   client = MAISClient.prod(client_cert)  # You can also use .uat() for UAT.
                                          # Or use .uat1() for UAT1.
   accounts = AccountClient(client)

   # Fetch an account
   lelandjr = accounts.get('lelandjr')  # This is one way, or …
   lelandjr = accounts['lelandjr']  # … you can do this!

   # Look at account information
   lelandjr.name  # "Stanford Jr., Leland"
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

Here is an example of how you can use the Workgroup API through this SDK:

.. code-block:: python

    from stanford.mais.client import MAISClient
    from stanford.mais.workgroup import WorkgroupClient
    from pathlib import Path

    # Keep this secret!
    client_cert = Path('client.pem')

    # Set up clients
    client = MAISClient.prod(client_cert)  # You can also use .uat() for UAT.
    workgroups = WorkgroupClient(client)

    # Fetch a workgroup
    sysadmins = workgroups.get('research-computing:sysadmins')
    sysadmins = workgroups['research-computing:sysadmins'] # This works too!

    # Create a workgroup
    if 'research-computing:everyone' not in workgroups:
        everyone = workgroups.create(
            name='research-computing:everyone',
            description='Everyone in Research Computing!',
            privgroup=True
        )
    else:
        everyone = workgroups['research-computing:everyone']

    # Workgroup members & administrators are sets, so you can use them like sets!
    missing_people = sysadmins.members.people - everyone.members.people
    if len(missing_people) > 0:
        print(
            'Some sysadmins are missing from everyone: ' +
            ','.join(missing_people)
        )
        everyone.members.people.update(sysadmins.members.people)

    # Adding people also uses set operations
    sysadmins.members.people.add(new_sysadmin)
    everyone.members.people.add(new_sysadmin)

    # Nesting workgroups also uses set operations
    everyone.members.workgroups.add('research-computing:sysadmins')

    # You can also access privgroups through this interface
    sysadmins_privgroup = sysadmins.get_privgroup()
    sysadmins_privgroup_members = sysadmins_privgroup.members
    ldap_accounts = list((member.sunetid for member in sysadmins_privgroup_members))

APIs Supported
--------------

The following APIs are supported:

* `Account`_: Full support for *Full Data* records for individual accounts,
  for both people (SUNetIDs) and functional accounts.  All of the information
  provided by the API is exposed, including service-specific settings.
  Support for 'views' that can act as if functional or inactive
  accounts don't exist (so you don't have to filter them out).  Also provided
  is code for quickly validating a collection of SUNetIDs.

  *Not implemented*: Retrieving a list of accounts that changed status in
  the past X days.

Work is in progress on the following APIs:

* `Workgroup`_: Full support for operations on individual workgroups.
  Creating workgroups.  Searching for workgroup by name, or by member (member
  SUNetID, member certificate, or member (nested) workgroup).
  Modifying workgroup properties and membership.  Deleting workgroups.
  Fetching privilege groups.  Checking and making linkages.

  *Not currently planned*: Anything related to workgroup integrations.

Support is not planned for the following APIs, as the author does not
currently have a need for them:

* `Course`_

* `Person`_

* `Privilege`_ (also known as "Authority")

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

* Python 3.11, or any later Python 3.x

  We will try to maintain support for whichever Python 3.x is present in the
  oldstable release of Debian.  Python 2 will not be supported.

* `Requests`_ 2.30.0, or any later 2.x.

  We do allow Requests 2.28.2, as packaged in Debian bookworm, but we do not
  currently test against it.

* A client certificate, issued by `MaIS`_, with permissions to the APIs you
  want to use, in the appropriate tier (such as PROD (production) or UAT).  See
  the `Getting Started`_ guide for more information.

* Testing requires `PyTest <https://docs.pytest.org/en/latest/>`_ and
  `pytest-responses <https://pypi.org/project/pytest-responses/>`_.

* Linting requires `MyPy <http://www.mypy-lang.org/>`_ and `types-requests
  <https://pypi.org/project/types-requests/>`_.

* Building documentation requires `Sphinx <http://www.sphinx-doc.org/>`_ and
  the `Sphinx RTD Theme <https://sphinx-rtd-theme.readthedocs.io>`_.

At this time, there is no explicit support for threads, multiple processes, or
async, though support may be added in the future.  Until then, you should be
safe to use these modules, so long as you don't share instances across
threads/processes.

.. _Requests: https://requests.readthedocs.io/
.. _MaIS: https://uit.stanford.edu/team/mais
.. _Getting Started: https://uit.stanford.edu/developers/apis/getting-started

Versions & Installation
-----------------------

Production releases are available through `PyPi`_.  The project name is
`stanford-mais`_.  `Semantic versioning`_ is used for production releases.

Non-production releases are available `on PyPi Test`_.  Non-production releases
use pre-release version numbers.  To install the latest-available pre-release
version, use a command like
``pip install -i https://test.pypi.org/simple/ stanford-mais --pre``.

.. _PyPi: https://pypi.org/
.. _stanford-mais: https://pypi.org/project/stanford-mais/
.. _Semantic versioning: https://semver.org
.. _on PyPi Test: https://test.pypi.org/project/stanford-mais/

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
