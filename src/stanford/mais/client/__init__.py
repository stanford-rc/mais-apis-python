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

import collections.abc
import dataclasses
import logging
import pathlib
import requests
import ssl
from typing import *

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info

# We are the root for this module, so do library-wide logging configuration.
# See https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger('stanford.mais.client').addHandler(logging.NullHandler())

# Define a Named Tuple for the most detailed form of timeout
class Timeout(NamedTuple):
    """A custom timeout for use with Requests.

    See `the Requests documentation`_ for more information on timeouts.

    .. _the Requests documentation: https://requests.readthedocs.io/en/latest/user/advanced/#timeouts
    """

    connect: float
    """The connection timeout.

    This should be larger than a multiple of 3.0, due to TCP mechanics.

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

    To instantiate a :class:`MAISClient`, you will need to provide two pieces
    of configuration as parameters to the class constructor.  The configuration
    items are documented below.

    For convenience, you may wish to use one of the ready-made constructors,
    :meth:`MAISClient.prod` and :meth:`MAISClient.uat`.
    :meth:`MAISClient.uat1` is also available for the temporary UAT1
    environment.  If you use one of those, then you do not need to provide the
    ``urls``.
    """

    urls: Mapping[str, str]
    """A mapping of API to URL.

    This mapping uses API names (like ``account``) as keys, and the base URL as
    the value.

    If you are setting up your own client instance, you will need to provide
    entries for each API you plan on using.  If you are using the UAT or PROD
    (production) environments, you can call :meth:`uat` or :meth:`prod`.  If
    you are using a different environment, or developing a MaIS API locally,
    you won't be able to use those methods, but you can study the code (more
    specifically, the URLs they embed) to get an idea of which URL is needed
    for which service.

    :raises TypeError: You did not provide a mapping.
    """

    cert: pathlib.Path
    """The path to a TLS client certificate.

    This may contain *either* a single TLS client certificate, *or* a TLS
    private key followed by a certificate.  The latter format (combined key and
    cert) was common in the old days; the former format (separate key and cert)
    is preferred today.

    The certificate (and key, if included) must be in PEM format (the text
    format).  If a key is included, and it is an EC key, then any necessary EC
    parameters may be included before the private key.

    A test load will be made before the constructor completes.

    .. note:
        If you provide your own ``session``, then this parameter is ignored,
        though the test will still be performed

    :raises FileNotFoundError: The file does not exist.

    :raises PermissionError: We do not have read permission on the file.

    :raises ssl.SSLError: The private key and certificate do not match, or there was some other problem loading the certificate.
    """

    key: Optional[pathlib.Path] = None
    """The path to a TLS private key.

    This must be the private key associated with the provided certificate, any
    must only be set if the private key is in a separate file from the
    certificate.  If the private key and certificate are in the same file, then
    this must be set to `None`.

    The file must be in PEM format (the text format), and must contain a single
    key.  If the key is an EC key, then any necessary EC parameters may be
    included, before the private key.  This is the same format that most
    programs (particularly web servers) use.

    .. warning::
       The private key must **not** be password-protected.  Enabling support
       for this is covered in `<https://github.com/psf/requests/issues/1573>`_.

    A test load of the key and certificate will be made before the constructor
    completes.

    .. note:
        If you provide your own ``session``, then this parameter is ignored.
        though the test will still be performed

    :raises FileNotFoundError: The file does not exist.

    :raises PermissionError: We do not have read permission on the file.

    :raises ssl.SSLError: The private key and certificate do not match, or there was some other problem loading the certificate.
    """

    session: requests.Session = dataclasses.field(repr=False, init=False)
    """The Requests Session to use for API requests.

    In most cases, you should not provide a Session during instance creation.
    The default behavior is to let the class constructor create the Session,
    using the ``cert``, (optional) ``key``, and ``default_timeout`` parameters.
    Some headers are also pre-configured.

    If you provide your own Session, then you are responsible for configuring
    it, and the ``cert``, ``key``, and ``timeout`` parameters are
    ignored.
    """

    timeout: Union[Timeout, float, None] = None
    """The timeout to use for requests.

    Requests `does`_ `not`_ `support`_ setting default timeouts, so we
    internally subclass :class:`requests.Session` to implement a default
    timeout.  This is the timeout that will be used.

    In addition, to match what Requests supports, we accept `None` (to not set
    a specific timeout) and a single float (covering both timeouts).

    There are two separate timeouts, a connect timeout and a read timeout.
    See the documentation of :class:`Timeout` for more information.

    You may either provide a single float (used for both timeouts), a
    :class:`Timeout` tuple (to specify different connect and read timeouts), or
    ``None`` (to not specify a timeout).

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

        # Check if cert is a string, and convert if needed.
        if not isinstance(self.cert, pathlib.Path):
            self.__dict__['cert'] = pathlib.Path(self.cert)

        # Try opening the file, to confirm it can be opened.
        with self.cert.open(mode='r') as f:
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
            # Set up a session with our cert/key, timeouts, and also specify
            # that we want JSON responses.

            new_session = _CustomSession()
            if self.key is None:
                new_session.cert = str(self.cert)
            else:
                new_session.cert = (
                    str(self.cert),
                    str(self.key),
                )
            if self.timeout is not None:
                new_session.timeout = self.timeout
            new_session.headers.update({
                'Accept': 'application/json',
            })
            object.__setattr__(self, 'session', new_session)
        else:
            debug('Using client-provided session')

        # That's it!
        return None

    @classmethod
    def prod(
        cls: Type['MAISClient'],
        cert: pathlib.Path,
        key: Optional[pathlib.Path] = None,
        timeout: Union[Timeout, float, None] = None,
    ) -> 'MAISClient':
        """Return a client configured to connect to connect to production
        (PROD) APIs.

        The returned client has all of the URLs pre-configured.

        .. note::
           A new client instance is created every time you call this.  If
           you want to take advantage of caching, call this only once per
           thread/process.

        :param cert: See :class:`MAISClient` for more information.

        :param key: See :class:`MAISClient` for more information.

        :param timeout: See :class:`MAISClient` for more information.

        :raises FileNotFoundError: The file does not exist.

        :raises PermissionError: We do not have read permission on the file.

        :raises ssl.SSLError: The private key and certificate do not match, or there was some other problem loading the certificate.
        """
        return cls(
            urls={
                'account': 'https://accountws.stanford.edu/accounts/',
                'course': 'https://registry.stanford.edu/doc/courseclass/',
                'person': 'https://registry.stanford.edu/doc/person/',
                'privilege': 'https://registry.stanford.edu/doc/privileges/',
                'student': 'https://studentws.stanford.edu/v1/person/',
                'workgroup': 'https://aswsweb.stanford.edu/mais/workgroupsvc/workgroups/2.0',
            },
            cert=cert,
            key=key,
            timeout=timeout,
        )

    @classmethod
    def uat(
        cls: Type['MAISClient'],
        cert: pathlib.Path,
        key: Optional[pathlib.Path] = None,
        timeout: Union[Timeout, float, None] = None,
    ) -> 'MAISClient':
        """Return a client configured to connect to connect to UAT APIs.

        The returned client has all of the URLs pre-configured.

        .. note::
           A new client instance is created every time you call this.  If
           you want to take advantage of caching, call this only once per
           thread/process.

        :param cert: See :class:`MAISClient` for more information.

        :param key: See :class:`MAISClient` for more information.

        :param timeout: See :class:`MAISClient` for more information.

        :raises FileNotFoundError: The file does not exist.

        :raises PermissionError: We do not have read permission on the file.

        :raises ssl.SSLError: The private key and certificate do not match, or there was some other problem loading the certificate.
        """
        return cls(
            urls={
                'account': 'https://accountws-uat.stanford.edu/accounts/',
                'course': 'https://registry-uat.stanford.edu/doc/courseclass/',
                'person': 'https://registry-uat.stanford.edu/doc/person/',
                'privilege': 'https://registry-uat.stanford.edu/doc/privileges/',
                'student': 'https://studentws-uat.stanford.edu/v1/person/',
                'workgroup': 'https://aswsuat.stanford.edu/mais/workgroupsvc/workgroups/2.0/',
            },
            cert=cert,
            key=key,
            timeout=timeout,
        )

    @classmethod
    def uat1(
        cls: Type['MAISClient'],
        cert: pathlib.Path,
        key: Optional[pathlib.Path] = None,
        timeout: Union[Timeout, float, None] = None,
    ) -> 'MAISClient':
        """Return a client configured to connect to connect to UAT1 APIs, used for Sequoia testing.

        The returned client has all of the URLs pre-configured.

        .. warning::
           There are no UAT1 APIs available for Course or Student, so those
           APIs are not available through this client.

        .. warning::
           The only UAT1 Workgroup API is the XML-based 1.0 API.  This Python
           package uses the JSON-based 2.0 API.  Therefore, this Python package
           will not work with UAT1 at this time.

        .. note::
           A new client instance is created every time you call this.  If
           you want to take advantage of caching, call this only once per
           thread/process.

        :param cert: See :class:`MAISClient` for more information.

        :param key: See :class:`MAISClient` for more information.

        :param timeout: See :class:`MAISClient` for more information.

        :raises FileNotFoundError: The file does not exist.

        :raises PermissionError: We do not have read permission on the file.

        :raises ssl.SSLError: The private key and certificate do not match, or there was some other problem loading the certificate.
        """
        return cls(
            urls={
                'account': 'https://accountws-uat.stanford.edu/accounts/',
                'person': 'https://registry-uat.stanford.edu/doc/person/',
                'privilege': 'https://registry-uat.stanford.edu/doc/privileges/',
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

    timeout: Union[None, float, Timeout] = None
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
