=========================
MaIS Client Configuration
=========================

All uses of this package begin by instantiating a
:class:`stanford.mais.client.MAISClient`.  But you should not instantiate the
class directly.  Instead, you should use one of the conveneice class methods
for the Environment you plan on accessing.

***********************
What is an Environment?
***********************

MaIS operates multiple instances of its services, grouped into *Environments*.
The Environment that everyone knows is ``PROD``, the production environment
accessible through URLs like `workgroup.stanford.edu`_ and
`accounts.stanford.edu`_.  Changes made in PROD propagate to downstream systems
like `Active Directory`_ and `LDAP`_, and to third-party systems like `Google
Groups`_.

.. _workgroup.stanford.edu: https://workgroup.stanford.edu

.. _accounts.stanford.edu: https://accounts.stanford.edu

.. _Active Directory: https://uit.stanford.edu/service/activedirectory

.. _LDAP: https://uit.stanford.edu/service/directory

.. _Google Groups: https://uit.stanford.edu/service/gsuite/groups

In addition to PROD, developers will often interact with the ``UAT``
Environment.  UAT (short for "User Acceptance Testing") is an environment with
production-quality data, but which does not touch downstream production
systems.  For example, changes in UAT will not affect production LDAP, but they
do propagate to a separate (UAT) LDAP environment.

UAT exists both for MaIS developers, and for clients: MaIS developers use UAT
as a final testing area before a change 'goes live' in PROD.  Clients use UAT
as a way to visualize changes they plan on making in PROD.  If they have a
separate non-production infrastructure, some clients also use MaIS' UAT
platform as their non-production infrastructure's 'source of truth', having
users authenticate via UAT Stanford Login, use UAT LDAP, use UAT Workgroup
Manager, etc.

MaIS developers also create their own environments, as needed for their work.
With proper configuration, this project (and the
:class:`~stanford.mais.client.MAISClient`) can access all of them.

**************
Authentication
**************

MaIS APIs use two different forms of authentication:

* **Client certificates**.  With client-certificate authentication, you create
  an RSA private key and TLS CSR.  MaIS issues you a certificate, using their
  private CA.  All API calls are authenticated using the private key and
  certificate.

  Certificates are enabled to only work with one environment
  (typically either PROD or UAT).  Within that environment, your certificate
  can be enabled to work with multiple services.  For example, you might have a
  certificate that can work with the UAT Account and UAT Workgroup APIs.

  Certificates are valid for several years.  When it comes close to
  expiration, MaIS notifies you by email.  You can then obtain a renewed
  certificate.

* **OAuth**.  With OAuth authentication, MaIS issues you an OAuth 2.0 Client ID
  and Client Secret.  You use the OAuth 2.0 client-credentials flow to obtain
  an OAuth access token.  All API calls are authenticated using the access
  token.

  OAuth Client IDs are enabled to work with only one environment (typically
  either PROD or UAT).  Within that environment, your Client ID can be enabled
  to work with multiple services.  For example, you might have a Client ID that
  can work with the UAT Account and UAT Workgroup APIs.

  Access tokens are valid for one hour.  We obtain an access token when the
  :class:`~stanford.mais.client.MAISClient` is instantiated.  After 55 minutes,
  the next API call will trigger a refresh of the access token.

  The OAuth Client ID and Client Secret do not expire.  However, as per `MinSec
  for SaaS/PaaS`_, you should obtain a new Client Secret at least once every
  year.

.. _MinSec for SaaS/PaaS: https://uit.stanford.edu/guide/securitystandards/saas_paas

API Transition
==============

MaIS is working to transition their APIs to using OAuth authentication.  That
means APIs can be in one of three different states:

1. The API only uses client-certificate authentication.

2. The API is available through two endpoints:

   * One endpoint uses client-certificate authentication.

   * One endpoint uses OAuth authentication.

3. The API only uses OAuth authentication.

Here is how this SDK is handling the transition:

* :class:`~stanford.mais.client.MAISClient` now supports recording both
  client-certificate and OAuth endpoint URLs for an API.  Also, the
  :class:`~stanford.mais.client.MAISClient` constructor now supports providing
  an OAuth Client ID and Client Secret, in addition to client certificate and
  private key.

  You can choose to provide either OAuth credentials or a client-certificate,
  or both.

* Each API client (for example, the
  :class:`~stanford.mais.account.AccountClient` or the
  :class:`~stanford.mais.workgroup.WorkgroupClient`) will either support
  client-certificate authentication, OAuth authentication, or both.

  If you try to instantiate a client, and you do not have the authentication
  credential required, the client will raise an exception.  The client's
  documentation will say what form of authentication it supports.

* When an OAuth endpoint is made available, the
  :class:`~stanford.mais.client.MAISClient` convenience methods
  :meth:`~stanford.mais.client.MAISClient.prod` and
  :meth:`~stanford.mais.client.MAISClient.uat` are updated to add the OAuth
  endpoint URLs.

* After a round of testing, the API's client is updated to support
  OAuth authentication.

  If an API client supports both OAuth authentication and client-certificate
  authentication, OAuth will be the preferred authenticaton method.

* When an API removes support for client-certificate authentication, that
  support will be removed from this SDK.

When OAuth support is added for an API, the :doc:`Changelog <changes>` will
be updated.  Similarly, when client-certificate support is removed from an API,
the :doc:`Changelog <changes>` will be updated.

**************
The MAISClient
**************

To get access to MaIS APIs, you will need a client certificate — or OAuth
client credential — with permissions to the appropriate service and
environment, and you will also need to instantiate a
:class:`~stanford.mais.client.MAISClient` using the appropriate class method.

For more information on how to obtain a client certificate, and get permission
to use MaIS APIs, read `Getting Started with the MaIS Web APIs`_.

.. _Getting Started with the MaIS Web APIs: https://uit.stanford.edu/developers/apis/getting-started

The :class:`~stanford.mais.client.MAISClient` class has three classmethods
available, for connecting to the three Environments that most users will use:

* :meth:`~stanford.mais.client.MAISClient.prod` connects you to MaIS'
  production APIs.  This is what you will probably use in production code.

* :meth:`~stanford.mais.client.MAISClient.uat` connects you to MaIS'
  UAT APIs.  This is what you will probably use during testing and development.

Here is a partial example (with parameters elided) showing how to access the
different MAIS Environments:

.. code-block:: python

   # A MAISClient connected to the PROD Environment
   client_prod = MAISClient.prod(...)

   # A MAISClient connected to UAT
   client_uat = MAISClient.uat(...)

   # This Account API client is connected to PROD
   aclient_prod = AccountClient(client_prod)

   # This Account API client is connected to UAT
   aclient_uat = AccountClient(client_uat)

The only difference between accessing PROD and accessing UAT, is in which
:class:`~stanford.mais.client.MAISClient` you instantiate.

Constructor Parameters
======================

All of the :class:`~stanford.mais.client.MAISClient` constructor class methods
take the same parameters:

* ``cert``: A path to a client certificate.

* ``key``: optional path to a client certificate key.

* ``client_id``: An OAuth 2.0 client ID.

* ``client_secret``: An OAuth 2.0 client secret.

To use OAuth client authentication, you must provide both ``client_id`` and
``client_secret``.  These must be the actual Client ID and Client Secret.  If
you need to read the ID and Secret from elsewhere (from files, or from the
environment), that is your responsibility.  If you are not using OAuth client
authentication, do not set ``client_id`` or ``client_secret`` (they will
default to ``None``).

To use client-certificate authentication, you must have the certificate and
private key in files.  You provide at least ``cert``.  If you are not using
client-certificate authentication, do not set ``cert`` (it will default to
``None``).

If you are using client-certificate authentication and the certificate's
private key is in a separate file, you must provide the path in ``key``.

``cert`` and ``key`` can be any "path-like" object, including a string or a
:class:`pathlib.Path`.

For example, here is a basic case, with client certificate and private key in
separate files, at hard-coded paths:

.. code-block:: python

   client = MAISClient.prod(
     cert='/etc/myapp/cert.pem',
     key='/etc/myapp/key.pem'
   )

If your path contains characters like `~` to refer to the user's home
directory, you should make the path into a :class:`pathlib.Path` and call
:meth:`pathlib.Path.expanduser` before passing it to the constructor.  You may
also wish to subsequently call :meth:`pathlib.Path.resolve` with
``strict=True`` to make the path absolute, and ensure it is valid.  For
example:

.. code-block:: python

   my_cert_and_key = pathlib.Path('~/symlink/app.pem')

   try:
     cert = my_cert_and_key.expanduser().resolve(strict=True)
     client = MAISClient.prod(
       cert=cert,
     )
   except OSError:
     print(f"Path `{my_cert_and_key}` not found")

The above example also shows how the :class:`~stanford.mais.client.MAISClient`
supports PEM files which contain the certficiate and its private key in a
single file.

.. tip::
   When the certificate and private key are in the same PEM file, the private
   key is placed after the certificate.

.. warning::
   The PEM format supports storing private keys in encrypted format, where a
   passphrase is needed to decrypt the private key.  This project does **not**
   support those types of private keys.

Timeouts
========

This package uses `Python Requests`_ to make API calls.  By default, Requests
does not have any explicit timeouts; timeouts are left up to the operating
system.  On Linux, for example, connections may take up to ~30 seconds to time
out, and open connections may wait for hours without reading data.

.. _Python Requests: https://requests.readthedocs.io

For more control over timeouts, the :class:`~stanford.mais.client.MAISClient`
constructor has the ``timeout`` parameter, giving you two options for setting a
timeout:

1. To specify a single timeout (in seconds), used for both connecting and
   reading data, provide a single float number as the timeout.

   .. important::
      This does not combine the two timeouts into one, it just specifies the same
      number for both timeouts.

2. To specify separate timeouts for connecting and reading, create an instance
   of the :class:`stanford.mais.client.Timeout` class and use that.

Here is an example of both methods:

.. code-block:: python

   # Long connect and read timeouts of 20 seconds each
   client1 = MAISClient.prod(
     cert='/etc/myapp/cert.pem',
     key='/etc/myapp/key.pem',
     timeout=20
   )

   # A short connect timeout (3.5 seconds); a long (20-second) read timeout
   client2 = MAISClient.prod(
     cert='/etc/myapp/cert.pem',
     key='/etc/myapp/key.pem',
     timeout=stanford.mais.client.Timeout(
       connect=3.5,
       read=20,
     )
   )

Custom Environments
===================

If you are a MaIS developer, you might wish to use a
:class:`~stanford.mais.client.MAISClient` with an environment that is not PROD,
UAT.  Hello!

This is the only situation in which you would call the
:class:`~stanford.mais.client.MAISClient` constructor directly, instead of
using one of its class methods (like
:meth:`~stanford.mais.client.MAISClient.prod` or
:meth:`~stanford.mais.client.MAISClient.uat`).  You will need to create a
:class:`~stanford.mais.client._URLs` instance, which is a
:class:`typing.TypedDict` containing one key for each MaIS API: The key is the
API name and the value is the base URL.

.. code-block:: python

   dev_environment = stanford.mais.client._URLs(
     account='https://localhost:4000/accounts/',
   )
   credentials = pathlib.Path(os.environ['devcert'])

   dev_client = MAISClient(
     cert=credentials.expanduser().resolve(strict=True),
     urls=dev_environment,
   )
   dev_account = AccountClient(dev_client)

.. tip::
   You may also wish to set a custom :class:`~stanford.mais.client.Timeout`.

********************
Module Documentation
********************

Here is detailed documentation for the ``stanford.mais.client`` module.

To begin using any of the MaIS API clients, you must first instantiate a
:class:`~stanford.mais.client.MAISClient`.  This stores configuration common to
all clients.

.. autoclass:: stanford.mais.client.MAISClient
   :members:

Depending on your application, you may wish to set a non-default timeout.  The
:class:`~stanford.mais.client.Timeout` class can help you do that.

.. autoclass:: stanford.mais.client.Timeout
   :members:

Finally, if you plan on instantiating a
:class:`~stanford.mais.client.MAISClient` that points to an Environment that
does not have a convenience function (like
:meth:`~stanford.mais.client.MAISClient.prod` or
:meth:`~stanford.mais.client.MAISClient.uat`), you will need to provide a
:class:`~stanford.mais.client._URLs`.

.. autoclass:: stanford.mais.client._URLs
   :members:

