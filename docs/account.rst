===========
Account API
===========

This is the documentation for the Python client for the MaIS Account API.
Everything on this page is located in the ``stanford.mais.account`` module.

To begin using the MaIS Account API, you should first instantiate a
:class:`~stanford.mais.client.MAISClient` object.  Once that is done, you can
use it to instantiate an :class:`stanford.mais.account.AccountClient`.

.. note::
   All Account instances are read-only.  You cannot use this SDK to create or
   change accounts.

******************
Account API Client
******************

You will use the :class:`~stanford.mais.account.AccountClient` instance to
access the Account API.  Instantiating a
:class:`~stanford.mais.account.AccountClient` is easy:

.. code-block:: python

    client = MAISClient(...)
    wclient = AccountClient(client)

For performance, the :class:`~stanford.mais.account.AccountClient`
maintains a cache of fetched accounts.  To clear the cache, call
:meth:`~stanford.mais.account.AccountClient.clear_cache`.

.. warning::
   Once you clear the cache, avoid using any Account instances that you might
   have used before!

Fetching Accounts
=================

Once you have a :class:`~stanford.mais.account.AccountClient`, there are
several ways you can access accounts.  The accounts you access will be
instances of the :class:`~stanford.mais.account.Account` class.

One way is to use the :meth:`~stanford.mais.account.AccountClient.get` method
to fetch an accounts, providing the username of the accounts that you want.

.. important::
   Usernames are all lowercase.

The
:class:`~stanford.mais.account.AccountClient` also implements the
`__getitem__` method, so instead of calling
:meth:`~stanford.mais.account.AccountClient.get` you can get accounts as
you would items from a dict.

Here is an example of the two ways you can get a account:

.. code-block:: python

    aclient = AccountClient(...)

    # These two operations give you the same Workgroup:
    lelandjr = aclient.get('lelandjr')
    lelandjr = aclient['lelandjr']

Account Views
-------------

Stanford accounts represent more than just people.  "Functional Accounts" exist
for services that need to act as an account.  Most applications only care about
people, so Account Views may be used to limit an
:class:`~stanford.mais.account.AccountClient` to just the types of accounts
that you want.

An Account View is enabled by calling the appropriate
:class:`~stanford.mais.account.AccountClient` method.  There are four Account
Views available:

* :meth:`~stanford.mais.account.AccountClient.only_active`: Limits fetching
  and existance tests to only active accounts.

* :meth:`~stanford.mais.account.AccountClient.only_inactive`: Limits fetching
  and existance tests to only *inactive* accounts.

* :meth:`~stanford.mais.account.AccountClient.only_people`: Limits fetching
  and existance tests to only accounts for people.

* :meth:`~stanford.mais.account.AccountClient.only_functional`: Limits
  fetching and existance tests to only functional accounts.

Each method returns a modified :class:`~stanford.mais.account.AccountClient`,
whose :meth:`~stanford.mais.account.AccountClient.get`, `__getitem__`, and
`__contains__` methods will only 'see' accounts matching the view you
requested.  If you try to call :meth:`~stanford.mais.account.AccountClient.get`
for an account that does not match the view you requested, a :class:`KeyError`
will be raised.

.. tip::
   Account Views can be chained together!

See the following example of Account Views in action:

.. code-block:: python

    # `lelandjr` is an inactive person account;
    # `functional` is an active functional account.

    aclient = AccountClient(...)
    'lelandjr' in aclient # True
    'functional' in aclient # True

    # Make an Account View limited to people:
    aclient_people = aclient.only_people()
    'lelandjr' in aclient_people # True
    'functional' in aclient_people # False

    # Account Views can be 'chained' together:
    aclient_active_people = aclient.only_people().only_active()
    'lelandjr' in aclient_active_people # False
    'functional' in aclient_active_people # False

    # To an Account View, non-matching accounts do not exist:
    lelandjr1 = aclient['lelandjr'] # works fine
    lelandjr2 = aclient_active_people['lelandjr'] # KeyError

Searching for Accounts
======================

The Account API provides limited support for searching for accounts.  You are
only able to check if an account exists, and you are only able to search for
accounts that have recently changed status.

Account Existence
-----------------

Instances of :class:`~stanford.mais.account.AccountClient` implement
:class:`~collections.abc.Container` functionality, so you can check for account
existence like so:

.. code-block:: python

    aclient = AccountClient(...)
    lelandjr_exists = (True if 'lelandjr' in aclient else False)

.. warning::
   This check respects any Account Views you have in place.  If you do an ``in``
   check on an Account View, you might get ``False`` even if the account
   actually exists!

Accounts who Changed Status
---------------------------

The Account API provides a way to search for accounts which have recently
changed status (where "recently" means "from 1 to 30 days ago").  You can
perform this search by calling the
:meth:`~stanford.mais.account.AccountClient.get_changed_status` method.
The method takes three parameters:

* ``days``: How far back to search, from 1 to 30.

* ``current_status``: One of ``active``, ``inactive``, or ``pending``, only
  accounts with this *current* status will be included in the results.

  .. note::
     ``pending`` is a status that accounts take when they are first created,
     and are not yet active.

  .. important::
     This search only counts the *current* status.  If an account has changed
     from active to inactive and back to active in the last 3 days, a search
     with ``days=5`` and ``current_status='inactive'`` will not include that
     account; the account had gone inactive within the search period, but it is
     not inactive *now*.

* ``get_people``: If True, only accounts for people are returned; if False,
  only functional accounts are returned.

The result of the search is a :class:`set`, so if you need to run the search
multiple times, you can combine results using unions.

This search returns "lite" account records, not full account records.  These
records are represented by the :class:`~stanford.mais.account.PartialAccount`
class, which contains the following properties:

* :attr:`~stanford.mais.account.PartialAccount.sunetid`: The account's
  username.

* :attr:`~stanford.mais.account.PartialAccount.is_person`: True if the account
  is for a person; False otherwise.

* :attr:`~stanford.mais.account.PartialAccount.is_active`: True if the account
  is active; False otherwise.

* :attr:`~stanford.mais.account.PartialAccount.last_update`: The last time the
  account was updated, as an aware :class:`~datetime.datetime`.

If you need the full :class:`~stanford.mais.account.Account`, you can fetch it
by calling the :meth:`~stanford.mais.account.PartialAccount.account` method.

For example, here is code that runs a search and outputs a list of usernames
(which are included in lite account records) and names (which are not):

.. code-block:: python

    aclient = AccountClient(...)

    results1 = aclient.get_changed_status(
      days=7,
      current_status='active',
      get_people=True
    )
    results2 = aclient.get_changed_status(
      days=7,
      current_status='active',
      get_people=False,
    )

    print("New accounts in the last 7 days:")
    for result in (results1 | results2):
      account = result.account(aclient)
      print(f"* {result.sunetid} ({account.name})")

SUNetID Validation
------------------

If you have a collection of SUNetIDs, and you want to confirm that they are all
SUNetIDs, you can use the validation function
:func:`stanford.mais.account.validate.validate`, which is in the
``stanford.mais.account.validate`` module.

The function takes two parameters:

1. Either a string, or a collection — a :class:`list`, :class:`tuple`,
   :class:`set`, or :class:`frozenset` — of strings.  If you provide a string,
   items in the string must be separated by whitespace.

2. An :class:`~stanford.mais.account.AccountClient`.

   .. warning::
      If you provide an Account View, validation will take that into account,
      and may provide unexpected results!

:func:`~stanford.mais.account.validate.validate` returns an
:class:`~stanford.mais.account.validate.AccountValidationResults`, with
usernames sorted into four properties:

* :attr:`~stanford.mais.account.validate.AccountValidationResults.full`: The
  SUNetIDs of active, full-service (or full-sponsored) accounts.

* :attr:`~stanford.mais.account.validate.AccountValidationResults.base`: The
  SUNetIDs of active, base-service (or base-sponsored) accounts.

* :attr:`~stanford.mais.account.validate.AccountValidationResults.inactive`:
  The SUNetIDs of inactive accounts.

* :attr:`~stanford.mais.account.validate.AccountValidationResults.unknown`:
  Usernames that are either functional accounts, or that are not accounts.

Each property is a collection of strings, where each string is a SUNetID
(except for
:attr:`~stanford.mais.account.validate.AccountValidationResults.unknown`, where
the strings *might* be functional account usernames).

*************
Account Class
*************

The :class:`~stanford.mais.account.Account` class represents "full" account
records.  They are obtained by using
:meth:`~stanford.mais.account.AccountClient.get`, or when upgrading a
:class:`~stanford.mais.account.PartialAccount` "lite" account record using
:meth:`~stanford.mais.account.PartialAccount.account`.

Properties
==========

Every :class:`~stanford.mais.account.Account` has properties, *all of which are
read-only*.

.. note::
   This section provides summaries only.  See the Module Documentation for
   details about each property!

* :attr:`~stanford.mais.account.Account.sunetid`: The account's username.  For
  accounts for people, this is a SUNetID.

* :attr:`~stanford.mais.account.Account.name`: The account's name.

* :attr:`~stanford.mais.account.Account.description`: For
  people, this is some combination of their Org name and position title; for
  functional accounts, this is a description set at the time of the account's
  creation.

* :attr:`~stanford.mais.account.Account.is_person`: If True, this is an account
  for a person; False otherwise.

* :attr:`~stanford.mais.account.Account.is_active`: If True, this account is
  active and may use Stanford services.

  .. important::
     Frozen person accounts are still considered active.

* :attr:`~stanford.mais.account.Account.last_update`: The
  :class:`~datetime.datetime` when the account (not the
  :class:`~stanford.mais.account.Account` instance, the actual underlying
  account) was last changed.

****************
Account Services
****************

In this context, a "service" represents a core University service that is made
available to an account.  For example, active accounts for people always have a
``kerberos`` service, while active functional accounts for the `Shared Email`_
service all have a ``seas`` service.

Services may have "settings" associated with them, which are key-value pairs.
Keys may be optional, and may be multi-valued.

.. note::
   When a service is not active, all service-specific settings become optional.

.. warning::
   When a service is inactive, not only do all service-specific settings become
   optional, but some services may have settings un-set when they go inactive.

To access the services for an account, obtain a
:class:`~stanford.mais.account.Account` instance for the account, and access
the :attr:`~stanford.mais.account.Account.services` property.

The :attr:`~stanford.mais.account.Account.services`
property is a :class:`~stanford.mais.account.account.AccountServiceTypes`,
which itself contains one property for every service.  If an account has the
service, the property will contain something; if the account does not have the
service, the property will be ``None``.

.. important::
   Just because a service does not exist for an account, does not mean that it
   *never* existed for an account.

Here is an example of how to look up an account's UNIX User ID (UID) number.
If the account does not have the kerberos service, or the service is not
active, then ``None`` is returned:

.. code-block:: python

   def get_uid(
     account: Account,
   ) -> int | None:
     if account.services.kerberos is None:
       return None
     elif account.services.kerberos.is_active is False:
       return None
     else:
       return account.services.kerberos.uid

Each service has its own class, subclasses of
:class:`~stanford.mais.account.service.AccountService`.  This class, and its
subclasses, exist in the ``stanford.mais.account.service`` module.

Service Status
==============

Every service contains a ``status`` property, which will return a
:class:`~stanford.mais.account.service.ServiceStatus`.  There are three
possible statuses:

* **active**: The service is active for the account.

* **frozen**: The account has the service, but may not use it at this time.

* **inactive**: This account does not have this service.

The :attr:`~stanford.mais.account.service.AccountService.is_active` property
will tell you if a service is active.

.. warning::

   Because of the existence of the frozen status, it is not safe to
   assume that if
   :attr:`~stanford.mais.account.service.AccountService.is_active` is False,
   that the service is inactive.

   Instead, consider using
   :attr:`~stanford.mais.account.service.AccountService.not_inactive`.

Popular Services
================

These are the services you will most likely care about.

.. note::
   This section provides summaries only.  See the Module Documentation for
   details about each service!

Kerberos
--------

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``kerberos``
| Service class: :class:`~stanford.mais.account.service.AccountServiceKerberos`

All active accounts for people will have this service.  Functional accounts for
CGI will also have this service.

The service has two settings, both required, and both single-valued:

* :attr:`~stanford.mais.account.service.AccountServiceKerberos.principal`: The
  name of the user's Kerberos principal.  This is normally the same as their
  SUNetID, and is *not scoped*.

* :attr:`~stanford.mais.account.service.AccountServiceKerberos.uid`: The
  account's UNIX UID number.

This is the only account which may 

SEAS
----

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``seas``
| Service class: :class:`~stanford.mais.account.service.AccountServiceSEAS`

The "Stanford Electronic Alias Service", this represents an active
*@stanford.edu* email address for the account.  People who have this service
have a full account (sponsored or not).  Functional accounts for shared email
also have this service.

The service has seven settings, which are single-valued unless noted:

.. warning::
   Many of these settings contain email addresses.  Unless noted, **do not send
   email to them** without authorization.

* :attr:`~stanford.mais.account.service.AccountServiceSEAS.sunetid`: Required,
  multi-valued.  One of the entries in the list will be the account's username
  (for people, the person's SUNetID).  Additional entries in this list are
  aliases, at which the user may also receive mail.

* :attr:`~stanford.mais.account.service.AccountServiceSEAS.sunetidpreferred`:
  Required.  This will be one of the entries from the
  :attr:`~stanford.mais.account.service.AccountServiceSEAS.sunetid` list, and
  is the identifier (after concatenating with ``@stanford.edu``) at which the
  account wishes to receive email.

  .. note::
     It is OK to send emails to this address.

* :attr:`~stanford.mais.account.service.AccountServiceSEAS.forward`: Optional.
  Single-valued, with multiple emails separated by a comma.  If present, emails
  received by this account will be forwarded to the email addresses contained
  herein.

* :attr:`~stanford.mais.account.service.AccountServiceSEAS.local`: Optional.
  The canonical, fully-qualified email address for the account's Stanford email
  box.

* :attr:`~stanford.mais.account.service.AccountServiceSEAS.emailsystem`:
  Optional.  The identifier of the service which hosts said mailbox.

* :attr:`~stanford.mais.account.service.AccountServiceSEAS.urirouteto`:
  Required.  When someone browses to ``https://stanford.edu/~username``, they
  will be directed to the URI contained herein.  If an empty string, the account has no associated URI.  If a relative URI, it is relative to
  ``https://web.stanford.edu/``.

Other Services
==============

These are services which will be of interest to specific groups of developers.

.. note::
   This section provides summaries only.  See the Module Documentation for
   details about each service!

Email
-----

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``email``
| Service class: :class:`~stanford.mais.account.service.AccountServiceEmail`

If active, the account has a Stanford personal electronic mailbox.  The
``seas`` service should also be active.

All this service's settings are obsolete, and should not be used.

Leland
------

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``leland``
| Service class: :class:`~stanford.mais.account.service.AccountServiceLeland`

Originally created for Stanford's Shared Computing environment, today it
represents access to `FarmShare`_.

.. _FarmShare: https://farmshare.stanford.edu/

All active full-service (and full-sponsored) accounts for people will have this
service.  This service is another way to tell if a person has a base or full
account.

The service has one required, single-valued setting:

* :attr:`~stanford.mais.account.service.AccountServiceLeland.shell`: The
  absolute path to the user's shell.

PTS
---

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``pts``
| Service class: :class:`~stanford.mais.account.service.AccountServicePTS`

This represents the accounts entry in the AFS ``ir`` cell's Protection Server.
People and CGI functional accounts will have this service.  This is required
for the account to access *any* AFS service at Stanford.

The service has one required, single-value setting:

* :attr:`~stanford.mais.account.service.AccountServicePTS.uid`: The UID number
  for the account.  It should be the same as the account's UID number in the
  kerberos service.

AFS
---

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``afs``
| Service class: :class:`~stanford.mais.account.service.AccountServiceAFS`

This represents an account's AFS home volume.  CGI functional accounts might
also have this service.

The service has one required, single-value setting:

* :attr:`~stanford.mais.account.service.AccountServiceAFS.homedirectory`: The
  absolute path to the account's AFS home directory in the ``ir`` cell.

Library
-------

| :class:`~stanford.mais.account.account.AccountServiceTypes` property name: ``library``
| Service class: :class:`~stanford.mais.account.service.AccountServiceLibrary`

This represents access to library e-resources, which full-service accounts
receive automatically, and which sponsored accounts may have granted to them.

The service has no settings.

Obsolete Services
=================

Two services are obsolete.  Accounts might still have one or more of these
services; they are listed here, and documented in Module Documentation.

* ``autoreply``: :class:`~stanford.mais.account.service.AccountServiceAutoreply`

* ``dialin``: :class:`~stanford.mais.account.service.AccountServiceDialin`

********************
Module Documentation
********************

stanford.mais.account
=====================

This module contains the :class:`~stanford.mais.account.AccountClient`, used to
access the Account API.

.. autoclass:: stanford.mais.account.AccountClient
   :members:

When searching for accounts which have changed status recently, the results
returned are instances of :class:`~stanford.mais.account.PartialAccount`,
representing "lite" account records.

.. autoclass:: stanford.mais.account.PartialAccount
   :members:

stanford.mais.account.account
=============================

.. autoclass:: stanford.mais.account.Account
   :members:

.. autoclass:: stanford.mais.account.account.AccountServiceTypes
   :members:

stanford.mais.account.service
=============================

.. automodule:: stanford.mais.account.service
   :members:

stanford.mais.account.validate
==============================

This module contains the :func:`~stanford.mais.account.validate.validate`
function, used to bulk-validate a collection of SUNetIDs.

.. autofunction:: stanford.mais.account.validate.validate

Validation results are returned via an instance of
:class:`~stanford.mais.account.validate.AccountValidationResults`.

.. autoclass:: stanford.mais.account.validate.AccountValidationResults
   :members:

