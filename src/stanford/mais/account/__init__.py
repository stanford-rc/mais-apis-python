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

import dataclasses
import logging
import requests
from typing import *
import stanford.mais.client
from .account import *

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warn = logger.warn

# We are the root for this module, so do library-wide logging configuration.
# See https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger('stanford.mais.account').addHandler(logging.NullHandler())

__all__ = (
    'AccountClient',
    'Account',
)

# First, define the client class.  Then, define the actual account.

@dataclasses.dataclass(frozen=True)
class AccountClient():
    """
    The :class:`AccountClient` is the first thing you will instantiate when you
    want to interact with the MaIS Account API.  One parameter is required to
    instantiate a client.

    :param stanford.mais.client.MAISClient client: The MAIS client to use.

    Once you have a client instantiated, you can use :meth:`get` to fetch an
    account.   For your convenience, instances of this class also implement
    `__getitem__`, so instead of doing…

    .. code-block:: default

       aclient = AccountClient(...)
       lelandjr = client.get('lelandjr')

    … you can do …

    .. code-block:: default

       aclient = AccountClient(...)
       lelandjr = client['lelandjr']

    Instances also implement :class:`~collections.abc.Container` functionality,
    so you can check for account existence like so:

    .. code-block:: default

       aclient = AccountClient(...)
       lelandjr_exists = (True if 'lelandjr' in client else False)

    Through the use of caching, if you then decide to fetch the account
    after confirming its existance, the entry will be served from cache
    instead of making a fresh API request.

    .. warning::

       The existence of an account does not mean it is active!
    """

    client: stanford.mais.client.MAISClient
    """A :class:`~stanford.mais.client.MAISClient` instance.

    This configures the API endpoint (accessed via `client.urls['account']`)
    and client key/cert to use.  It must be provided when calling the class
    constructor.

    :raises TypeError: A client was not provided.
    """

    session: Optional[requests.Session] = dataclasses.field(repr=False, default=None)
    """The Requests Session to use for API requests.

    This session container pre-configures our requests, including client
    certificate, timeouts, and headers.

    This need not be provided at init-time, but it can be (which is useful for
    mock testing).  If left unset (which is the default), a new session will be
    requested from the client.
    """

    _cache: Mapping[str, 'Account'] = dataclasses.field(repr=False, default_factory=dict)
    """Cache of already-seen accounts.

    This cache is used to store :class:`Account` instances already seen by this
    client.  It speeds up repeated accesses of accounts.
    """

    def __post_init__(self) -> None:
        """Check provided constructor variables.

        This checks the provided client, and (if needed) sets up the Requests
        session.

        :raises TypeError: A client was not provided.
        """

        # Check the client type
        if not isinstance(self.client, stanford.mais.client.MAISClient):
            raise TypeError('client')

        # Make a new Requests session (if it's not already provided), and
        # configure it.
        if self.session is None:
            self.__dict__['session'] = self.client.session()
        self.session.headers.update({'Accept': 'application/json'})

        # That's it!
        return None

    def get(
        self,
        sunetid: str,
    ) -> 'Account':
        """Fetch an Account.

        This is a convenience wrapper around :meth:`Account.get`, which
        provides this client as the `client`.  All other parameters provided
        are passed through to :meth:`Account.get`, and the resulting instance
        is returned.

        Refer to :meth:`~Account.get` for details on parameters, exceptions,
        etc..
        """
        return Account.get(
            client=self,
            sunetid=sunetid,
        )

    def __getitem__(
        self,
        item: str,
    ) -> 'Account':
        """Fetch an Account.

        This works exactly like :meth:`get`.  See :meth:`get` and
        :meth:`Account.get` for more information.
        """
        return self.get(item)

    def __contains__(
        self,
        sunetid: str
    ) -> bool:
        """Check for SUNetID existance.

        :param sunid: The account ID to check for existence.

        :return: `True` if the account exists, else `False`.
        """
        try:
            self.get(sunetid)
            return True
        except KeyError:
            return False

    # Now, let's create some AccountViews!!!

    def only_active(
        self,
    ) -> 'AccountView':
        """Create a modified ``AccountClient`` that can only see active
        accounts.

        The returned client instance has been modified so that
        :meth:`~AccountClient.get` only returns active accounts.  If you
        try to look up an inactive account, :meth:`~AccountClient.get` will
        act as if the account does not exist.

        As many Account API consumers are only interested in active accounts,
        you may find this to be very convenient.  If this interests you, you
        can do something like this:

        .. code-block:: default

           import stanford.mais.client
           from stanford.mais.client.account import AccountClient

           api_client = stanford.mais.client.MAISClient(...)
           active_accounts = AccountClient(api_client).only_active()

        .. warning::
           The 'client' returned by this method uses the same caches as this
           client.  Therefore, it must not be used across threads/processes.
        """
        return AccountView(
            client=self.client,
            session=self.session,
            _cache=self._cache,
            account_filter=lambda candidate: (True if candidate.is_active else False)
        )

    def only_inactive(
        self,
    ) -> 'AccountView':
        """Create a modified ``AccountClient`` that can only see inactive
        accounts.

        The returned client instance has been modified so that
        :meth:`~AccountClient.get` only returns inactive accounts.  If you
        try to look up an active account, :meth:`~AccountClient.get` will
        act as if the account does not exist.

        .. warning::
           The 'client' returned by this method uses the same caches as this
           client.  Therefore, it must not be used across threads/processes.
        """
        return AccountView(
            client=self.client,
            session=self.session,
            _cache=self._cache,
            account_filter=lambda candidate: (True if candidate.is_active else False)
        )

    def only_people(
        self,
    ) -> 'AccountView':
        """Create a modified ``AccountClient`` that can only see accounts of
        people.

        The returned client instance has been modified so that
        :meth:`~AccountClient.get` only returns the accounts of people.  If you
        try to look up a functional account, :meth:`~AccountClient.get` will
        act as if the account does not exist.

        As many Account API consumers are only interested in SUNetIDs,
        you may find this to be very convenient.  If this interests you, you
        can do something like this:

        .. code-block:: default

           import stanford.mais.client
           from stanford.mais.client.account import AccountClient

           api_client = stanford.mais.client.MAISClient(...)
           sunetids = AccountClient(api_client).only_people()

        And, if you only care about active SUNetIDs, you can chain them
        together, like this:

        .. code-block:: default

           import stanford.mais.client
           from stanford.mais.client.account import AccountClient

           api_client = stanford.mais.client.MAISClient(...)
           active_sunetids = AccountClient(api_client).only_active().only_people()

        .. warning::
           The 'client' returned by this method uses the same caches as this
           client.  Therefore, it must not be used across threads/processes.
        """
        return AccountView(
            client=self.client,
            session=self.session,
            _cache=self._cache,
            account_filter=lambda candidate: (True if candidate.is_person else False)
        )

    def only_functional(
        self,
    ) -> 'AccountView':
        """Create a modified ``AccountClient`` that can only see functional
        accounts.

        The returned client instance has been modified so that
        :meth:`~AccountClient.get` only returns functional accounts.  If you
        try to look up a person's account (a SUNetID),
        :meth:`~AccountClient.get` will act as if the account does not exist.

        .. warning::
           The 'client' returned by this method uses the same caches as this
           client.  Therefore, it must not be used across threads/processes.
        """
        return AccountView(
            client=self.client,
            session=self.session,
            _cache=self._cache,
            account_filter=lambda candidate: (False if candidate.is_person else True)
        )

# This is where the accounts views functionality is implemented.
# Although this class is fully documented, it is not intended for direct use by
# clients.

class AccountView(AccountClient):
    """Create a new view into the Accounts API.

    This has the same mandatory parameters as :class:`AccountClient`,
    meaning you must at least provide a ``client`` parameter, but in
    addition you must also provide a filter function.

    The filter function must take an :class:`Account` as its only
    parameter, and return a :class:`bool`.  If the filter function returns
    ``False``, this view will act as if the account does not exist.

    :param account_filter: The filter function.
    """

    def __init__(
        self,
        account_filter: Callable[['Account'], bool],
        *args,
        **kwargs
    ) -> None:
        # Set up the AccountClient as normal
        super().__init__(*args, **kwargs)

        # Add the filter function
        self.account_filter = account_filter

    def get(
        self,
        sunetid: str
    ) -> Account:
        """Fetch an Account.

        This is a **modified** convenience wrapper around
        :meth:`AccountClient.get`, which provides this client as the `client`.
        All other parameters provided are passed through to
        :meth:`AccountClient.get`.

        If an account is found, it is passed to the filter function.  If the
        filter function returns ``True``, the account will be returned to the
        caller; if the filter function returns ``False``, a :class:`KeyError`
        will be raised.

        Refer to :meth:`Account.get` for details on parameters, exceptions,
        etc..

        :raises KeyError: Either the account does not exist, or it does not match the filter.
        """
        candidate = super().get(sunetid)
        if self.account_filter(candidate) is True:
            return candidate
        else:
            raise KeyError(sunetid)
