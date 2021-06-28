============
Accounts API
============

This is the documentation for the Python client for the MaIS Accounts API.
Everything you need is available in the :mod:`stanford.mais.account` module.

To begin using the MaIS Accounts API, you should first instantiate a
:class:`~stanford.mais.client.MAISClient` object.  Once that is done, you can
use it to instantiate a :class:`~stanford.mais.account.AccountClient` object.

.. _Account API Client:

Account API Client
==================

You will use the :class:`~stanford.mais.account.AccountClient` instance to
access the API.  Once that is done, you can use the
:meth:`~stanford.mais.account.AccountClient.get` method to access
:ref:`Accounts <Account>`.

.. autoclass:: stanford.mais.account.AccountClient
   :members:

.. _Account:

Account
=======

Once you have a Account API client instance, you will be fetching
:class:`~stanford.mais.account.Account` instances.

All account attributes will be found within the
:class:`~stanford.mais.account.Account` instance.  Service-specific information
will be found within the :meth:`~stanford.mais.account.Account.services`
dict, which will present a different interface depending on the service.
:ref:`Read more about services <Account Services>`.

.. autoclass:: stanford.mais.account.Account
   :members:

.. _Account Services:

Account Services
================

Accounts normally have at least one service attached.  For example, active
accounts have a ``kerberos`` service active.  Even inactive accounts might have
services attached, although those services will all be inactive.

Services are accessed through
:meth:`~stanford.mais.account.Account.services`, like so:

.. code-block:: python

   aclient = stanford.mais.account.AccountClient(...)
   lelandjr = aclient['lelandjr']
   if lelandjr.services.kerberos is None:
       lelandjr_uid = None
   else:
       lelandjr_uid = lelandjr.services.kerberos.uid

:meth:`~stanford.mais.account.Account.services` acts as a named tuple, with an
attribute for each service that the Python MsIS Account API client is aware of.
Through these attributes, you can access service status and
service-specific settings.  For example, the ``kerberos`` service maps to the
:class:`~stanford.mais.account.service.AccountServiceKerberos` class.

If an account does not have a service defined, accessing that attribute will
return ``None``.

.. note::
   When an account is a functional account, and not an account for a person,
   there is no guarantee what services will be enabled.  For example, a
   functional account used for a web site's CGI space will have ``kerberos``,
   ``pts``, and possibly ``afs`` service; a functional account used for shared
   email will not have any of those, but *will* have ``seas`` service.

.. warning::
   When a service is active, some service-specific settings are guaranteed to
   be present, and some are optional.  **However**, when a service is not
   active, *all service-specific settings become optional*.

.. automodule:: stanford.mais.account.service
   :members:

.. _Account Validation:

Accounts Validation
===================

The :class:`~stanford.mais.account.Account` class provides all of the tools
needed to validate a single SUNetID (that is, determine if it is a valid
SUNetID).  But if you have a list of SUNetIDs (particularly an unformatted
list), the :mod:`stanford.mais.account.validate` module has function that can
help.

.. automodule:: stanford.mais.account.validate
   :members:
