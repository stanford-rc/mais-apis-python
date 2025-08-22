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
from collections.abc import Callable, MutableMapping
import dataclasses
import logging
import requests

# Finally, do local imports
from stanford.mais.account.account import Account
import stanford.mais.client

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warn = logger.warning

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

    The :class:`AccountClient` is the second thing you will instantiate when you
    want to interact with the MaIS Account API.  (The first thing you
    instantiate is a :class:`MAISClient`).  Once you have a
    :class:`MAISClient`, you pass it to the :class:`AccountClient` constructor
    with this parameter:

    :param stanford.mais.client.MAISClient client: The MAIS client to use.

    Once you have an :class:`AccountClient` instantiated, you can use
    :meth:`get` to fetch an account.   For your convenience, instances of this
    class also implement ``__getitem__``, so instead of doing…

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
       lelandjr_exists = (True if 'lelandjr' in aclient else False)

    Through the use of caching, if you then decide to fetch the account
    after confirming its existance, the entry will be served from cache
    instead of making a fresh API request.

    .. warning::
       The existence of an account does not mean it is active!
    """

    client: stanford.mais.client.MAISClient
    """A :class:`~stanford.mais.client.MAISClient` instance.

    This configures the API endpoint (accessed via ``client.urls['account']``)
    and client key/cert to use.  It must be provided when calling the class
    constructor.

    :raises TypeError: A client was not provided.
    """

    _cache: MutableMapping[str, Account] = dataclasses.field(repr=False, default_factory=dict)
    """Cache of already-seen accounts.

    This cache is used to store :class:`Account` instances already seen by this
    client.  It speeds up repeated accesses of accounts.
    """

    _filters: frozenset[Callable[[Account], bool]] = dataclasses.field(repr=False, default_factory=frozenset)
    """Set of filters to apply on lookups.

    The callables in this frozen set are evaluated when ``get()`` is called,
    and has found an Account.  Each callable will be called with the Account as
    the only parameter.  If any callable returns a ``False``, then a
    ``KeyError`` will be raised, as if the lookup failed.

    .. note::

       If a callable returns ``False``, then there is no guarantee that all
       callables will be called before the exception is raised.  The only
       situation where all callables will be called is when all callables
       return ``True``.
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

        # That's it!
        return None

    def get(
        self,
        sunetid: str,
    ) -> Account:
        """Fetch an Account.

        This is a convenience wrapper around :meth:`Account.get`.  All other
        parameters provided are passed through to :meth:`~Account.get`, and the
        resulting instance is returned.

        Refer to :meth:`Account.get` for details on parameters, exceptions,
        etc..
        """
        # Fetch our account
        account = Account.get(
            client=self,
            sunetid=sunetid,
        )

        # Check against filters
        for filter_func in self._filters:
            if filter_func(account) is False:
                raise KeyError(sunetid)

        # All filters passed!
        return account

    def __getitem__(
        self,
        item: str,
    ) -> Account:
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

    def clear_cache(
        self,
    ) -> None:
        """Clear cache of accounts.

        As mentioned in the class docs, visited accounts are cached locally,
        for speed and to reduce load on the Account API.  Although accounts
        rarely change, in long-running
        programs, this can be a problem.  To assist, this method clears the
        cache of this specific Account client.

        .. danger::
            If you are holding a reference to an existing :class:`Account`,
            or to one of the the Account's services, clearing the cache does
            not invalidate those references!

            This method should not be called unless you know what you are
            doing.
        """
        debug('in clear_cache')
        self._cache.clear()

    # Now, let's create some AccountViews!!!

    def only_active(
        self,
    ) -> AccountClient:
        """Create a modified :class:`AccountClient` that can only see active
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

        .. tip::
           You can stack these filters.  For example,
           ``AccountClient(api_client).only_active().only_people()`` will only
           be able to "see" active people accounts (ignoring active functional
           accounts).

        .. warning::
           The 'client' returned by this method uses the same caches as this
           client.  Therefore, it must not be used across threads/processes.
        """
        new_filter = lambda candidate: (True if candidate.is_active else False) 
        return AccountClient(
            client=self.client,
            _cache=self._cache,
            _filters=self._filters | frozenset((new_filter,))
        )

    def only_inactive(
        self,
    ) -> AccountClient:
        """Create a modified :class:`AccountClient` that can only see inactive
        accounts.

        The returned client instance has been modified so that
        :meth:`~AccountClient.get` only returns inactive accounts.  If you
        try to look up an active account, :meth:`~AccountClient.get` will
        act as if the account does not exist.

        See :meth:`~AccountClient.only_active` for examples, tips, and
        warnings.
        """
        new_filter = lambda candidate: (False if candidate.is_active else True) 
        return AccountClient(
            client=self.client,
            _cache=self._cache,
            _filters=self._filters | frozenset((new_filter,))
        )

    def only_people(
        self,
    ) -> AccountClient:
        """Create a modified :class:`AccountClient` that can only see
        accounts of people.

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
        new_filter = lambda candidate: (True if candidate.is_person else False) 
        return AccountClient(
            client=self.client,
            _cache=self._cache,
            _filters=self._filters | frozenset((new_filter,))
        )

    def only_functional(
        self,
    ) -> AccountClient:
        """Create a modified :class:`AccountClient` that can only see
        functional accounts.

        The returned client instance has been modified so that
        :meth:`~AccountClient.get` only returns functional accounts.  If you
        try to look up a person's account (a SUNetID),
        :meth:`~AccountClient.get` will act as if the account does not exist.

        See :meth:`~AccountClient.only_people` for examples, tips, and
        warnings.
        """
        new_filter = lambda candidate: (False if candidate.is_person else True) 
        return AccountClient(
            client=self.client,
            _cache=self._cache,
            _filters=self._filters | frozenset((new_filter,))
        )
