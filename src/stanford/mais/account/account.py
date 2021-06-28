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

import abc
import dataclasses
import datetime
import enum
import logging
import requests
from typing import *
import urllib.parse
from . import service

# Some imports are only needed when typechecking
if TYPE_CHECKING:
    from . import AccountClient

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warn = logger.warn

# NOTE: It's expected that this module will be *-imported, so not only does this
# define what gets included in Sphinx docs, this also determines what gets
# *-imported.
__all__ = (
    'Account',
)

# The Account class is big!  So it's in its own file.
# (_AccountServiceTypes is here as required support.)

class AccountServiceTypes(NamedTuple):
    """The different types of services which may be attached to an Account.

    Since not all services may be associated with an account, these are all
    marked as optional.
    """

    kerberos: Optional[service.AccountServiceKerberos]
    library: Optional[service.AccountServiceLibrary]
    seas: Optional[service.AccountServiceSEAS]
    email: Optional[service.AccountServiceEmail]
    autoreply: Optional[service.AccountServiceAutoreply]
    leland: Optional[service.AccountServiceLeland]
    pts: Optional[service.AccountServicePTS]
    afs: Optional[service.AccountServiceAFS]
    dialin: Optional[service.AccountServiceDialin]

@dataclasses.dataclass(frozen=True)
class Account():
    """A SUNetID Account.

    The entire contents are read-only.

    .. note::
       Information from the Account API is generally mapped to attributes in
       the `Accounts Tree`_ in `Stanford LDAP`_.

    .. _Accounts Tree: https://uit.stanford.edu/service/directory/datadefs/accounts

    .. _Stanford LDAP: https://uit.stanford.edu/service/directory
    """

    client: 'AccountClient'
    """
    The :class:`AccountClient` representing the API endpoint we are using.
    """

    sunetid: str
    """
    The SUNetID, for people; for functional accounts, the ID.  This is the `id`
    key from the API.

    .. note::
       This is used as the account's ``uid`` in LDAP.
    """

    name: str
    """
    For people, this is ther name (last name first).  For functional accounts,
    this is a name set at the time of account creation.  This is the `name` key
    from the API.
    """

    description: str
    """
    For people, this is a combination of their Org name and their position
    title.  This may be set to "Former …" or the like for inactive accounts
    For functional accounts, this is a description set at the time of account
    creation.  This is the `description` key from the API.

    .. note::
       This is used as the account's ``description`` in LDAP.
    """

    is_person: bool
    """
    If `True`, this account is for a person.  If `False`, this account is for a
    "functional account".  This is the `type` key from the API.
    """

    is_active: bool
    """
    If `True`, this SUNetID is active.  In other words, someone could
    authenticate to Stanford Login using this SUNetID.  This does not imply
    anything else.  This is computed from the `status` key from the API.
    """

    is_full: bool
    """
    If `True`, this is a full SUNetID.  That means the SUNetID has services
    like email enabled.  A SUNetID can be "full" either by being associated
    with an active student, faculty, or staff member; or via sponsorship.
    *NOTE*: Some services (such as Library e-resources) are not available to
    all Full SUNetIDs, so this property does not imply access to *all*
    services.
    """

    services: AccountServiceTypes
    """
    This contains the services currently associated with the account.  Each
    service has a service name, and the value is a dataclass which contains
    status and service-specific information.
    """

    last_updated: datetime.datetime
    """
    The datetime when the account was last updated.  It is timezone-aware, and
    is already set to the UTC timezone.
    """

    raw: dict[str, Any]
    """
    This is the parsed JSON returned from the MaIS Accounts API.  Most keys
    have already been parsed, and are available as properties.  Here are some
    additional keys you can find:

    * **owner**: This is a string with two parts, with a forward-slash used as a
      separator.

      * If the account is for a person (that is, `type` is "self"), then this
        string will be `person/` followed by the RegID of the person.

      * If the account is for a functional account (`type` is "functional"),
        then this string will be `organization/` followed by the RegID of the
        Org which owns the functional account.

    * **statusDate**: The date when this account was last changed, in the
      US/Pacific time zone, in the form of a POSIX timestamp tht has been
      multiplied by 1,000 and microseconds added on to the end.  You can parse
      this using :meth:`datetime.datetime.fromtimestamp` and the third-party
      :meth:`pytz.timezone` as follows:

      .. code-block:: python

         statusDateInt=account.raw['statusDate']
         statusDate=datetime.datetime.fromtimestamp(
            statusDateInt//(10**3),
            tz=pytz.timezone('US/Pacific')
         ).replace(
            microsecond=statusDateInt%(10**3)
         ).astimezone(
            pytz.utc
         )

      You really should just use :meth:`last_updated` instead.
    """

    @classmethod
    def get(
        cls: Type['Account'],
        client: 'AccountClient',
        sunetid: str,
    ) -> 'Account':
        """Given a string, return an Account.

        This uses the MaIS Workgroup API to look up information for an account,
        using the SUNetID as input.

        This function is memoized; once a lookup is performed, subsequent calls
        for the same input will return the same result instance, thanks to the
        use of a cache.

        *WARNING*: This will looks up accounts of all types, both accounts for
        people and also functional accounts.  Check the :meth:`type` before
        assuming you are working with a SUNetID.

        *WARNING*: This memoization means that, should an account change status
        after lookup, that status change will not be noticed until after the
        module is reloaded.  That means this code should *not* be used by
        long-running client code.

        :param client: An :class:`AccountClient` representing our API endpoint.

        :param sunetid: The to look up.  This must be an actual id, not an alias.

        :raises ChildProcessError: Something went wrong on the server side (a 400 or 500 error was returned).

        :raises IndexError: The input is too long.  Maybe the input is an alias?

        :raises KeyError: The given SUNetID does not exist.

        :raises PermissionError: You did not use a valid certificate, or do not have permissions to perform the operation.

        :raises ValueError: The input contains non-ASCII characters.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        debug(f"In get with input '{sunetid}'")

        # Do we have the account in cache?  If yes, return it!
        if sunetid in client._cache:
            debug(f"Returning account {sunetid} from cache!")
            return client._cache[sunetid]

        # Make sure the SUNetID is ASCII
        try:
            sunetid.encode('ascii')
        except UnicodeEncodeError:
            raise ValueError(f"String '{sunetid}' contains non-ASCII characters")

        # If the 'SUNetID' ends in @stanford.edu, strip that off.
        # Then recurse, to get the benefit of memoization.
        if sunetid.endswith('@stanford.edu'):
            debug(f"Cleaning up an email address")
            sunetid = sunetid.removesuffix('@stanford.edu')
            return cls.get(client=client, sunetid=sunetid)

        # Now it's time to try fetching the account information!

        # Get the Requests session
        session = client.session

        # Make the request for the SUNetID.
        info(f"Fetching {sunetid} from the Account API…")
        response = session.get(
            urllib.parse.urljoin(client.client.urls['account'], sunetid),
            timeout=client.client._default_timeout,
        )

        # Catch a number of bad errors.
        debug(f"Status code is {response.status_code}")
        if response.status_code in (400, 500):
            raise ChildProcessError(response.text)
        if response.status_code in (401, 403):
            raise PermissionError(sunetid)
        if response.status_code == 404:
            raise KeyError(sunetid)

        # Decode the JSON
        info('Parsing response JSON')
        response_json = response.json()

        # Process the services associated with the account.

        # First, define a table of known services, mapping each to its class.
        known_services: Dict[str, Type[service.AccountService]] = {
            'kerberos': service.AccountServiceKerberos,
            'library': service.AccountServiceLibrary,
            'seas': service.AccountServiceSEAS,
            'email': service.AccountServiceEmail,
            'autoreply': service.AccountServiceAutoreply,
            'leland': service.AccountServiceLeland,
            'pts': service.AccountServicePTS,
            'afs': service.AccountServiceAFS,
            'dialin': service.AccountServiceDialin,
        }

        # Next, create a container for services, with `None` for each known
        # service.
        services = dict((k,None) for k in known_services.keys())

        # Look at what services are associated with the account.
        # For each one, call the service class's constructor.
        # Do this now so we can reference them later.
        for service_dict in response_json['services']:
            service_name = service_dict['name']
            # This next check is in case we find a service we don't know about.
            if service_name in known_services:
                service_constructor = known_services[service_name]._from_json
                services[service_name] = service_constructor(service_dict)
            else:
                warn(f"Ignoring unknown service f{service_name}")

        # Is the account full?  If the leland service is active, then yes.
        is_full = False
        if services['leland'] is not None:
            if services['leland'].is_active is True:
                is_full = True

        # Is the account for a person, or functional?
        account_type = response_json['type']
        if account_type == 'self':
            is_person = True
        elif account_type == 'functional':
            is_person = False
        else:
            raise NotImplementedError(f"Unexpected account type '{account_type}'")

        # Compute last_updated
        last_updated=datetime.datetime.strptime(
            response_json['statusDateStr'],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).replace(tzinfo=datetime.timezone.utc)

        # Construct, add to cache, and return the object
        result = Account(
            client=client,
            sunetid=response_json['id'],
            name=response_json['name'],
            description=response_json['description'],
            is_person=is_person,
            is_active=(True if response_json['status'] == 'active' else False),
            is_full=is_full,
            services=AccountServiceTypes(**services),
            last_updated=last_updated,
            raw=response_json,
        )
        client._cache[sunetid] = result
        return result

    def __repr__(self) -> str:
        return f"Account.get({self.sunetid})"
