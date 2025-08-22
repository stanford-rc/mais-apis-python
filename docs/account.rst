===========
Account API
===========

This is the documentation for the Python client for the MaIS Account API.
Everything on this page is located in the :mod:`stanford.mais.account` module.

To begin using the MaIS Account API, you should first instantiate a
:class:`~stanford.mais.client.MAISClient` object.  Once that is done, you can
use it to instantiate an :class:`~stanford.mais.account.AccountClient` object,
which you use to look up accounts.

Each account is returned as an instance of the
:class:`~stanford.mais.account.Account` class.

.. note::
   All Account instances are read-only.  You cannot use this SDK to create or
   change accounts.

.. _Account API Client:

Account API Client
==================

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
accounts have a ``kerberos`` service, in either active or frozen status.

.. warning::
   Inactive accounts might have services attached, although those services will
   all be inactive.  Also, active accounts might have inactive services
   attached (:class:`~stanford.mais.account.service.AccountServiceAutoreply`
   is a good example of this).

Services are accessed through
:data:`~stanford.mais.account.Account.services`, like so:

.. code-block:: python

   aclient = stanford.mais.account.AccountClient(...)
   lelandjr = aclient['lelandjr']
   if lelandjr.services.kerberos is None:
       lelandjr_uid = None
   elif lelandjr.services.kerberos.is_active is False:
       lelandjr_uid = None
   else:
       lelandjr_uid = lelandjr.services.kerberos.uid

.. warning::
   When a service is active, some service-specific settings are guaranteed to
   be present, and some are optional.  **However**, when a service is not
   active, *all service-specific settings become optional*.

The following services are recognized, and have the following
:class:`~stanford.mais.account.service.AccountService` subclasses:

* ``kerberos``: :class:`~stanford.mais.account.service.AccountServiceKerberos`

* ``library``: :class:`~stanford.mais.account.service.AccountServiceLibrary`

* ``seas``: :class:`~stanford.mais.account.service.AccountServiceSEAS`

* ``email``: :class:`~stanford.mais.account.service.AccountServiceEmail`

* ``autoreply``: :class:`~stanford.mais.account.service.AccountServiceAutoreply`

* ``leland``: :class:`~stanford.mais.account.service.AccountServiceLeland`

* ``pts``: :class:`~stanford.mais.account.service.AccountServicePTS`

* ``afs``: :class:`~stanford.mais.account.service.AccountServiceAFS`

* ``dialin``: :class:`~stanford.mais.account.service.AccountServiceDialin`

If an account does not have a service defined, accessing that attribute will
return ``None``.

.. note::
   When an account is a functional account, and not an account for a person,
   there is no guarantee what services will be enabled.  For example, a
   functional account used for a web site's CGI space will have ``kerberos``,
   ``pts``, and possibly ``afs`` service; a functional account used for shared
   email will not have any of those, but *will* have ``seas`` service.

.. automodule:: stanford.mais.account.service
   :members:

.. _Account Validation:

Account Validation
==================

If you have a set of IDs, and you want to confirm that they are all SUNetIDs,
you can use the validation function in the :mod:`stanford.mais.account.validate` module.
The function will identify which accounts are full SUNetIDs, base SUNetIDs,
inactive SUNetIDs, and others (functional accounts and invalid usernames).

.. automodule:: stanford.mais.account.validate
   :members:
