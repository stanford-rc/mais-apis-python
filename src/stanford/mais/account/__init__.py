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
import datetime
import dataclasses
import logging
import requests
from typing import Literal
import urllib.parse

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


# Define a type for search results
@dataclasses.dataclass(frozen=True, slots=True)
class PartialAccount:
    """Part of a Stanford Account.

    This is a "lite" account record.  Lite accounts are returned by the
    Workgroup API in two cases:

    * When you fetch a lite account, instead of a full account (we never do
      this).

    * When you request a list of accounts that have changed status recently.

    The entire contents are read-only.

    To get the full account, call the :meth:`~PartialAccount.account` method to
    getch a full account record.
    """

    sunetid: str
    """
    For people, their SUNetID is also their username.  For functional accounts,
    this is their username.  This is the ``id`` key from the API.

    .. tip::
       This is used as the account's ``uid`` in LDAP.
    """

    is_person: bool
    """
    If `True`, this account is for a person.  If `False`, this account is for a
    "functional account".  This is the ``type`` key from the API.
    """

    is_active: bool
    """
    If `True`, this account is active.  If the account is for a person, then
    assuming the person's kerberos service is not frozen or otherwise blocked,
    they are able to use Stanford Login.  If the account is a functional
    account, then the associated services are active.  This does not imply
    anything else.  This is computed from the ``status`` key from the API.
    """

    last_update: datetime.datetime
    """
    The timezone-aware datetime when the account was last updated.  This is
    computed from the ``statusDateStr`` key from the API.
    """

    @classmethod
    def from_json(
        cls,
        source: dict[str, str | int],
    ) -> PartialAccount:
        debug(f"Creating PartialAccount for source['type'] {source['id']} ")

        # Check sunetid type
        if not isinstance(source['id'], str):
            raise TypeError('Unexpected type for "id"')

        # Is the account for a person, or functional?
        account_type = source['type']
        if not isinstance(account_type, str):
            raise TypeError('Unexpected type for "type"')
        if account_type == 'self':
            is_person = True
        elif account_type == 'functional':
            is_person = False
        else:
            raise NotImplementedError(f"Unexpected account type '{account_type}'")

        # Compute last_updated
        if not isinstance(source['statusDateStr'], str):
            raise TypeError('Unexpected type for "statusDateStr"')
        last_update=datetime.datetime.strptime(
            source['statusDateStr'],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).replace(tzinfo=datetime.timezone.utc)

        return cls(
            sunetid=source['id'],
            is_person=is_person,
            is_active=(True if source['status'] == 'active' else False),
            last_update=last_update,
        )

    def account(
        self,
        client: AccountClient,
    ) -> Account:
        """Fetch the full :class:`Account` for this search result.

        This is a convenience method, performing a normal account lookup and
        returning the result.

        .. warning::
           The returned Account may have a different `is_active` or
           `last_update` value.  Once you call this method, you should stop
           using this PartialAccount.

        .. note::
           The returned Account will have the same `is_person` value as this
           partial account.

        :param client: The AccountClient to use for the lookup.

        :returns: The full :class:`Account` for this PartialAccount's SUNetID.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises KeyError: The SUNetID changed between now and when this
            PartialAccount was returned in search results.  This is extremely
            rare.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.  This is also rare, and
            means you either changed certificates, or your certificate has been
            disabled or expired.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        return client.get(self.sunetid)

# Next, define the client class.  Then, define the actual account.

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

    # Accounts changed status in the last X days

    def get_changed_status(
        self,
        days: int,
        current_status: Literal['active', 'inactive', 'pending'],
        get_people: bool = True,
    ) -> frozenset[PartialAccount]:
        """Search for accounts which have recently changed status.

        Search for all accounts that have changed status within the specified number
        of days.  This is commonly used to get a list of accounts that have
        changed status

        .. warning::
           This call **only** includes accounts which have changed status.
           Changes to other attributes—like a person's name, or a service
           setting like email aliases—will not cause an account to be included
           in these results.

        .. warning::
           The search results will tell you which accounts changed status, but
           they will not tell you the old status.

        .. note::
           This method is not affected by the modified AccountClient instances
           returned by :meth:`only_active`, :meth:`only_inactive`,
           :meth:`only_people`, and :meth:`only_functional`.

        :param days: Include accounts that changed status within this many days.
            Must be at least 1, and at most 30.

        :param current_status: Only accounts with this current status will be
            included in the results.

            The status `pending` refers to an account which has just been
            created and is not yet active.  It is only used at the very
            beginning of an account's life cycle.

            .. note::
               Only one `current_status` value may be provided.  If you want a
               list of *all* accounts which have changed status, run this search
               multiple times (once for each status), and perform a set union
               on the results.

            .. warning::
               It is possible for an account to change status multiple times
               during your search period.  For example, if you search for
               `current_status` ``active``, your search results might include
               accounts which were already active, went inactive, and then
               became active again.

        :param get_people: If True (which is the defaut), only accounts for
            people will be included in the results.  If you instead want
            results for functional accounts, change this to ``False``.

            .. note::
               The search can return either people accounts or functional
               accounts, not both.  If you want both, then make two searches
               and perform a set union on the results.

        :raises ValueError: You provided an invalid `days`.

        :raises PermissionError: You did not use a valid certificate, or do not have permissions to perform the operation.

        :raises NotImplementedError: An unexpected HTTP response was received.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """

        # Check days
        if days < 1:
            raise ValueError('days must be at least 1')
        if days > 30:
            raise ValueError('days must be at most 30')

        # Get the Requests session
        session = self.client.session

        # Do the search.
        query = {
            'type': ('self' if get_people is True else 'functional'),
            'status': current_status,
            'statusdays': str(days),
        }
        info(f"Fetching all {query['type']} changed to {current_status} in the last {days} days…")
        response = session.get(
            urllib.parse.urljoin(
                self.client.urls['account'],
                '?' + urllib.parse.urlencode(query),
            ),
        )

        # Catch a number of bad errors.
        debug(f"Status code is {response.status_code}")
        match response.status_code:
            case 400 | 500:
                raise ChildProcessError(response.text)
            case 401 | 403:
                raise PermissionError(response.text)
            case _ if response.status_code != 200:
                raise NotImplementedError(response.text)

        # Decode the JSON
        info('Parsing response JSON')
        response_json = response.json()

        # Make our results
        return frozenset(list(
            (PartialAccount.from_json(result) for result in response_json)
        ))
