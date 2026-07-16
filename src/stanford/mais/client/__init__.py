# vim: ts=4 sw=4 et
# -*- coding: utf-8 -*-

# © 2021 The Board of Trustees of the Leland Stanford Junior University.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# This file has a ton of references to classes that are defined in the same
# file.  Pythons older than 3.14 (which implements PEP 649) cannot handle that
# natively without this import.
# NOTE: At some point in the future, this annodation will be deprecated.
from __future__ import annotations

# Start with stdlib imports
import collections.abc
import dataclasses
import importlib.metadata
import logging
import os
import platform
import requests
import ssl
from typing import NamedTuple, TypedDict

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info

# We are the root for this module, so do library-wide logging configuration.
# See https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger('stanford.mais.client').addHandler(logging.NullHandler())

# Define our custom user-agent, a static string
USER_AGENT = ' '.join((
    ('Python/' + platform.python_version()),
    ('requests/' + importlib.metadata.version('requests')),
    ('stanford-mais/' + importlib.metadata.version('stanford-mais')),
))

# Define types for our URLs
class _URLAuthMethod(TypedDict, total=False):
    """The different methods for authenticating to a MaIS API.

    Some MaIS APIs are accessed using client-certificate authentication, some
    are accessed using OAuth authentication, and those APIs that are in
    transition can be accessed by using either authentication method.
    """
    cert: str
    oauth: str

class _URLs(TypedDict, total=False):
    """The different services that MaIS provides, and their API endpoints.

    .. note::
       Just because a service is listed here, does not mean this package
       supports it.
    """
    account: _URLAuthMethod
    course: _URLAuthMethod
    person: _URLAuthMethod
    privilege: _URLAuthMethod
    student: _URLAuthMethod
    workgroup: _URLAuthMethod

# Define a Named Tuple for the most detailed form of timeout
class Timeout(NamedTuple):
    """Allows providing granular timeouts when making web requests.

    This library uses Requests to make HTTPS calls.  Requests has a peculiar
    way for dealing with timeouts.  See `the Requests documentation`_ for more
    information on timeouts.

    If you want to configure granular timeouts, you may do so using this class.
    The instance of this class is then passed to the :class:`MAISClient`
    constructor.

    .. _the Requests documentation: https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
    """

    connect: float
    """The connection timeout.

    How long to wait for the TCP connection to open.  This should be larger
    than a multiple of 3.0, due to TCP mechanics.

    .. warning::
       If connecting to a DNS name which has multiple IPs, each IP will be
       tried, and so the total timeout will be this value multiplied by the
       number of IPs.
    """

    read: float
    """The read timeout.

    How long to wait for data, once the request has been sent off.  This
    timeout resets whenever a single byte of data is received from the server.
    """

# This class primarily defines our API endpoints, and related general stuff
# that is not specific to any one MaIS API. 

@dataclasses.dataclass(frozen=True)
class MAISClient():
    """
    The :class:`MAISClient` is the first thing you will instantiate when you
    want to interact with a MaIS API.

    **You probably do not want to call this directly.** For convenience, you
    should one of the ready-made constructors, :meth:`MAISClient.prod` and
    :meth:`MAISClient.uat`.

    This class is documented here only to be a reference for the
    parameters you will need to provide when using a convenience constructor
    (in particular, ``cert``, ``key``, and ``timeout``).
    """

    urls: _URLs
    """A mapping of API to URL.

    This mapping uses API names (like ``account``) as keys.  The values are
    dicts that can have up to two keys:

    * If the `cert` key is present, this is the URL to use for
    certificate-based authentication.
    * If the `oauth` key is present, this is the URL to use for OAuth-based
    authentication.

    If both keys are present, the URL used will depend on if the user provides
    a certificate or an OAuth client, with OAuth being preferred over
    certificate.

    If you decided to not use the convenience constructors
    (:meth:`MAISClient.prod`, etc.), then you will need to provide entries for
    each API you plan on using.

    :raises TypeError: You did not provide a mapping.
    """

    cert: os.PathLike
    """The path to a TLS client certificate.

    This may contain *either* a single TLS client certificate, *or* a TLS
    private key followed by a certificate.  The combined format (key and
    cert in one file) was common in the old days; the former format (key and
    cert in separate files) is often preferred today.

    The certificate (and key, if included) must be in PEM format (the text
    format that has "BEGIN" and "END" lines).

    A test load will be made before the constructor completes.

    .. note::
        If you provide your own ``session``, then this parameter is ignored,
        though the test will still be performed.

    .. warning::
        If you provide a non-absolute path, it may not be relative to a
        home directory (like ``~``), or to a variable (like ``%UserProfile%``).
        If you have such a path, run it through :meth:`pathlib.Path.resolve`
        first.

    :raises FileNotFoundError: The file does not exist.

    :raises PermissionError: You do not have read permission on the file.

    :raises ssl.SSLError: The private key and certificate do not match, or
        there was some other problem loading the certificate.
    """

    key: os.PathLike | None = None
    """The path to a TLS private key.

    This must be the private key associated with the provided certificate, any
    must only be set if the private key is in a separate file from the
    certificate.  If the private key and certificate are in the same file, then
    this must be set to ``None``.

    The file must be in PEM format (the text format that has "BEGIN" and "END"
    lines), and must contain a single key.

    .. warning::
       The private key must **not** be password-protected.  Enabling support
       for this is covered in `<https://github.com/psf/requests/issues/2519>`_.

    A test load of the key and certificate will be made before the constructor
    completes.

    .. note::
        If you provide your own ``session``, then this parameter is ignored.
        though the test will still be performed

    .. warning::
        If you provide a non-absolute path, it may not be relative to a
        home directory (like ``~``), or to a variable (like ``%UserProfile%``).
        If you have such a path, run it through :meth:`pathlib.Path.resolve`
        first.

    :raises FileNotFoundError: The file does not exist.

    :raises PermissionError: We do not have read permission on the file.

    :raises ssl.SSLError: The private key and certificate do not match, or
        there was some other problem loading the certificate.
    """

    session: requests.Session = dataclasses.field(repr=False, init=False)
    """The Requests Session to use for API requests.

    In most cases, you should not provide a Session during instance creation.
    The default behavior is to let the class constructor create the Session,
    using the ``cert``, (optional) ``key``, and ``default_timeout`` parameters.
    Some headers are also pre-configured.

    If you provide your own Session, then you are responsible for configuring
    it, and the ``cert``, ``key``, and ``timeout`` parameters are
    ignored.  You must also set the `Accept` header to `application/json`, and
    you should also set the `User-Agent` header.
    """

    timeout: Timeout | float | None = None
    """The timeout to use for requests.

    Requests `does`_ `not`_ `support`_ setting default timeouts, so we
    internally subclass :class:`requests.Session` to implement a default
    timeout.  This is the timeout that will be used.

    In addition, to match what Requests supports, we accept ``None`` (to not set
    a specific timeout) and a single float (covering both timeouts).

    There are two separate timeouts, a connect timeout and a read timeout.
    See the documentation of :class:`Timeout` for more information.

    .. _does: https://github.com/psf/requests/issues/1130

    .. _not: https://github.com/psf/requests/issues/2856

    .. _support: https://github.com/psf/requests/issues/3054
    """

    def __post_init__(
        self,
    ) -> None:
        debug(f"In post_init for MAISClient")

        # Check if `urls` is a mapping.
        if not isinstance(self.urls, collections.abc.Mapping):
            raise TypeError('urls')

        # Try opening the file, to confirm it can be opened.
        with open(self.cert, mode='r') as f:
            pass

        # Try to parse the client certificate.
        sslc = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if self.key is None:
            sslc.load_cert_chain(str(self.cert))
        else:
            sslc.load_cert_chain(
                str(self.cert),
                keyfile=str(self.key),
            )

        # Do we need to create our own Session?
        if not hasattr(self, 'session'):
            debug('Creating Session')
            new_session = _CustomSession()

            # Set up our cert/key.
            if self.key is None:
                new_session.cert = str(self.cert)
            else:
                new_session.cert = (
                    str(self.cert),
                    str(self.key),
                )

            # Set up custom timeouts, if provided.
            if self.timeout is not None:
                new_session.timeout = self.timeout

            # Ask for JSON responses
            new_session.headers.update({
                'Accept': 'application/json',
            })

            # Set our custom user-agent
            new_session.headers.update({
                'User-Agent': USER_AGENT,
            })

            # Finally, put the new session into place
            object.__setattr__(self, 'session', new_session)
        else:
            debug('Using client-provided session')

        # That's it!
        return None

    @classmethod
    def prod(
        cls,
        cert: os.PathLike,
        key: os.PathLike | None = None,
        timeout: Timeout | float | None = None,
    ) -> MAISClient:
        """Return a client configured to connect to production (PROD) APIs.

        The returned client has all of the URLs pre-configured.

        .. note::
           A new client instance is created every time you call this.  If
           you want to take advantage of caching, call this only once per
           thread.

        :param cert: See :class:`MAISClient` for more information.

        :param key: See :class:`MAISClient` for more information.

        :param timeout: See :class:`MAISClient` for more information.

        :raises FileNotFoundError: The file does not exist.

        :raises PermissionError: We do not have read permission on the file.

        :raises ssl.SSLError: The private key and certificate do not match, or
            there was some other problem loading the certificate.
        """
        return cls(
            urls={
                'account': {
                    'cert': 'https://accountws.stanford.edu/accounts/',
                },
                'course': {
                    'cert': 'https://registry.stanford.edu/doc/courseclass/',
                },
                'person': {
                    'cert': 'https://registry.stanford.edu/doc/person/',
                },
                'privilege': {
                    'cert': 'https://registry.stanford.edu/doc/privileges/',
                },
                'student': {
                    'cert': 'https://studentws.stanford.edu/v1/person/',
                },
                'workgroup': {
                    'cert': 'https://workgroupsvc.stanford.edu/workgroups/2.0/',
                },
            },
            cert=cert,
            key=key,
            timeout=timeout,
        )

    @classmethod
    def uat(
        cls,
        cert: os.PathLike,
        key: os.PathLike | None = None,
        timeout: Timeout | float | None = None,
    ) -> MAISClient:
        """Return a client configured to connect to production-track test (UAT)
        APIs.

        The returned client has all of the URLs pre-configured.

        .. note::
           A new client instance is created every time you call this.  If
           you want to take advantage of caching, call this only once per
           thread.

        :param cert: See :class:`MAISClient` for more information.

        :param key: See :class:`MAISClient` for more information.

        :param timeout: See :class:`MAISClient` for more information.

        :raises FileNotFoundError: The file does not exist.

        :raises PermissionError: We do not have read permission on the file.

        :raises ssl.SSLError: The private key and certificate do not match, or
            there was some other problem loading the certificate.
        """
        return cls(
            urls={
                'account': {
                    'cert': 'https://accountws-uat.stanford.edu/accounts/',
                },
                'course': {
                    'cert': 'https://registry-uat.stanford.edu/doc/courseclass/',
                },
                'person': {
                    'cert': 'https://registry-uat.stanford.edu/doc/person/',
                },
                'privilege': {
                    'cert': 'https://registry-uat.stanford.edu/doc/privileges/',
                },
                'student': {
                    'cert': 'https://studentws-uat.stanford.edu/v1/person/',
                },
                'workgroup': {
                    'cert': 'https://workgroupsvc-uat.stanford.edu/workgroups/2.0/',
                },
            },
            cert=cert,
            key=key,
            timeout=timeout,
        )

# Create a custom Requests Session class

class _CustomSession(requests.Session):
    """A custom Requests Session, with a default timeout.

    Support for adding a timeout in a Session has been asked `many`_ `times`_
    `before`_, but it not going to be implemented.  So, this class does that.

    .. note:
        If you provide your own ``session``, then this parameter is ignored.

    .. _many: https://github.com/psf/requests/issues/1130

    .. _times: https://github.com/psf/requests/issues/2856

    .. _before: https://github.com/psf/requests/issues/3054
    """

    timeout: Timeout | float | None = None
    """The timeout value that so many folks wish Session had.

    This can be one of three things:

    * `None`, which means to not specify a timeout.

    * A tuple of two floats, both of which are seconds.  The first is for the
      initial connection; the second is for reading.  See :class:`Timeout` for
      details.

    * A single float, used for both the connect and read timeouts.

    See `the Requests documentation`_ for more information on timeouts.

    .. _the Requests documentation: https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
    """

    def send(
        self,
        request: requests.PreparedRequest,
        **kwargs,
    ) -> requests.Response:
        """ Send a prepared Request, but possibly add a timeout

        When a :class:`requests.Session` handles a
        :meth:`~requests.Session.request`, the timeout is sent through as a
        keyword argument to :meth:`~requests.Session.send`.  So, in order to
        insert our default timeout, we override :meth:`~requests.Session.send`.

        If the request was made with a timeout, we do not change that.
        """

        # Add our custom timeout, if one is not already provided
        if ('timeout' not in kwargs) or (kwargs['timeout'] is None):
            # Only set a timeout if we have one to set
            if self.timeout is not None:
                kwargs['timeout'] = self.timeout

        # Send the modified request, and return its Response
        return super().send(
            request,
            **kwargs
        )
