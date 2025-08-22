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

from collections.abc import Collection, Mapping, MutableMapping
import dataclasses
import datetime
import enum
import logging
import pathlib
import requests
from typing import Literal
import urllib.parse
import weakref
import stanford.mais.client
from stanford.mais.workgroup.workgroup import Workgroup

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error

# We are the root for this module, so do library-wide logging configuration.
# See https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger('stanford.mais.workgroup').addHandler(logging.NullHandler())

__all__ = (
    'WorkgroupClient',
    'Workgroup',
)

# Define the type for search results

def _now() -> datetime.datetime:
    return datetime.datetime.now(tz=datetime.timezone.utc)
@dataclasses.dataclass(
    frozen=True,
)
class PartialWorkgroup:
    """Part of a Stanford Workgroup.

    This contains the most basic parts of a workgroup.  It is what is returned
    whenever someone does a search for a workgroup.

    .. warning::
        Instances of this class are only accurate at the time of the
        instance's creation!  
    """

    name: str
    """The fully-qualified workgroup name.
    """

    description: str
    """The workgroup's description, which may be empty.
    """

    last_update: datetime.date
    """The date when the workgroup was last updated.

        .. warning::
            This date is in the Stanford-local time zone.  Remember to take
            this into account when doing comparisons.

        .. note::
            Why is it a date, instead of a datetime?  Because that is what the
            Workgroup API provides.
    """

    as_of: datetime.datetime = dataclasses.field(default_factory=_now)
    """The datetime when this search result was generated.
    """

    def __str__(self) -> str:
        return f"{self.name} (last updated {self.last_update}): {self.description}"

    def workgroup(
        self,
        client: 'WorkgroupClient',
    ) -> 'Workgroup':
        """Return the full :class:`Workgroup` object.

        This returns the full :class:`Workgroup` object for this
        PartialWorkgroup.  It is a convenience wrapper around the 
        :meth:`WorkgroupClient.get` method.
        """
        return client.get(self.name)


@dataclasses.dataclass(
    frozen=True,
)
class SearchByResults():
    is_member: frozenset[PartialWorkgroup]
    """Partial workgroups where the search target is a member.
    """

    is_administrator: frozenset[PartialWorkgroup]
    """Partial workgroups where the search target is an administrator.
    """


# Finally, define the client class.


@dataclasses.dataclass(frozen=True)
class WorkgroupClient():
    """
    The :class:`WorkgroupClient` is the first thing you will instantiate when
    you want to interact with the MaIS Workgroup API.  One parameter is required
    to instantiate a client.

    :param stanford.mais.client.MAISClient client: The MAIS client to use.

    Once you have a client instantiated, you can use :meth:`get` to fetch a
    workgroup.   For your convenience, instances of this class also implement
    ``__getitem__``, so instead of doing…

    .. code-block:: python

       wclient = WorkgroupClient(...)
       nero_users = wclient.get('nero:users')

    … you can do …

    .. code-block:: python

       wclient = WorkgroupClient(...)
       nero_users = wclient['nero:users']

    Instances also implement :class:`~collections.abc.Container` functionality,
    so you can check for workgroup existence like so:

    .. code-block:: python

       wclient = WorkgroupClient(...)
       nero_users_exists = (True if 'nero:users' in wclient else False)

    Through the use of caching, if you then decide to fetch the workgroup
    after confirming its existance, the entry will be served from cache
    instead of making a fresh API request.

    .. note::
        Take care in how you use this code, given that workgroups are cached.
        Should you be concerned about the accuracy of a cached
        :class:`Workgroup`, feel free to :meth:`Workgroup.refresh` it.

    Each instance provides the following attributes:
    """

    client: stanford.mais.client.MAISClient
    """A :class:`~stanford.mais.client.MAISClient` instance.

    This configures the API endpoint (accessed via ``client.urls['workgroup']``)
    and client key/cert to use.  It must be provided when calling the class
    constructor.
    """

    _cache: MutableMapping[str, weakref.ReferenceType['Workgroup']] = dataclasses.field(repr=False, default_factory=dict)
    """Cache of already-seen workgroups.

    This cache is used to store :class:`Workgroup` instances already seen by this
    client.  It speeds up repeated accesses of workgroups.
    """

    def __post_init__(self) -> None:
        """Check provided constructor variables.

        This checks the provided client, and (if needed) sets up the Requests
        session.

        :raises TypeError: A client was not provided.
        """
        debug('In __post_init__')

        # Check the client type
        if not isinstance(self.client, stanford.mais.client.MAISClient):
            raise TypeError('client')

        # That's it!
        return None

    def create(
        self,
        *args,
        **kwargs,
    ) -> Workgroup:
        """Create a Workgroup.

        This is a convenience wrapper around :meth:`Workgroup.create`.  All other
        parameters provided are passed through to :meth:`~Workgroup.create`, and the
        resulting instance is returned.

        .. note::
            When calling :meth:`Workgroup.create`, this convenience method will
            provide the ``client`` parameter for you.  You are responsible for
            providing all other parameters.

        Refer to :meth:`Workgroup.create` for details on parameters, exceptions,
        etc..
        """

        # This instance is acting as the client, so set that keyword argument.
        kwargs['client'] = self

        # Make the call!
        return Workgroup.create(
            *args,
            **kwargs
        )

    def get(
        self,
        name: str,
    ) -> Workgroup:
        """Fetch a Workgroup.

        This is a convenience wrapper around :meth:`Workgroup.get`.  The
        workgroup name you provide is passed through to :meth:`~Workgroup.get`,
        and the resulting instance is returned.

        .. note::
            If the workgroup you are requesting is already available in the
            cache, the cached instance will be returned instead.

        You can also use dict-style key access, like so:

        .. code-block:: default

           wclient = WorkgroupClient(...)
           nero_users = wclient['nero:users']

        Refer to :meth:`Workgroup.get` for details on exceptions, etc..
        """
        debug(f"In get for workgroup '{name}'")

        # Is the Workgroup in the cache?
        if name in self._cache:
            possible_workgroup = self._cache[name]()
            if possible_workgroup is not None:
                debug(f"Returning workgroup {name} from cache")
                return possible_workgroup
            else:
                del self._cache[name]

        # Get the Workgroup, store in cache, and return
        actual_workgroup = Workgroup.get(
            client=self,
            name=name,
        )
        self._cache[name] = weakref.ref(actual_workgroup)
        return actual_workgroup

    def __getitem__(
        self,
        name: str,
    ) -> Workgroup:
        """Fetch a Workgroup.

        This works exactly like :meth:`get`.  See :meth:`get` and
        :meth:`Workgroup.get` for more information.
        """
        return self.get(name)

    def __contains__(
        self,
        name: str
    ) -> bool:
        """Check for Workgroup existance.

        :param name: The workgroup name to check for existence.

        :return: `True` if the workgroup exists, else `False`.
        """
        debug(f"In __contains__ for workgroup '{name}'")
        try:
            self.get(name)
            debug('Workgroup found')
            return True
        except KeyError:
            debug('Workgroup not found')
            return False

    def search_by_name(
        self,
        search: str,
    ) -> Collection[PartialWorkgroup]:
        """Search for workgroups by name, with wildcards supported.

        :param search: The string to search for.  ``*`` is the wildcard symbol.

            To limit your search to a specific stem, provide the stem name and
            colon before the first wildcard.  For example, to list all
            workgroups in stem ``abc``, search for ``abc:*``.  To search for
            all Research Computing sysadmin workgroups, search for
            ``research-computing:sysadmins*``.

            To search across all stems, you may omit the ``*``.  However, you
            must provide at least for characters before the first wildcard.
            For exaple, ``mais*`` will work, but ``mai*`` will fail.

            You may have multiple wildcards in your search.

        :returns: A collection of partial workgroups.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).  This exception is also raised if
            you are doing a not-stem-limited search, and you do not have at
            least 4 characters before the first wildcard.

        :raises KeyError: The workgroup does not exist.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises ValueError: The search string began with an asterisk, or
            was empty.
        :raises ValueError: The input contains non-ASCII characters.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """

        # Make sure the search string is not empty, and does not start with an
        # asterisk.
        if len(search) == 0:
            raise ValueError('Search string is empty')
        if search[0] == '*':
            raise ValueError('Search string cannot begin with an asterisk')

        # Make our search URL fragment
        get_fragment = pathlib.PurePosixPath(
            'search',
            search,
        )

        # Make the request for the Workgroup.
        get_url = self._url(
            fragment=get_fragment,
        )
        debug(f"Doing GET of {get_url}")
        response = self.client.session.get(
            get_url,
        )

        # Catch a number of bad errors.
        if response.status_code in (400, 500):
            error(f"Upstream API error: {response.text}")
            raise ChildProcessError(response.text)
        if response.status_code in (401, 403):
            warning(f"Permission error on search for {search}")
            raise PermissionError(search)

        # Decode the JSON, and send to make the instance
        debug('Got a response!')
        response_json = response.json()
        search_results = response_json['results']

        # Make a space for search results, and make our partial workgroups
        results: set['PartialWorkgroup'] = set()
        for result in search_results:
            # Make a partial workgroup, and add to the results
            result = PartialWorkgroup(
                name=result['name'],
                description=('' if 'description' not in result else result['description']),
                last_update=Workgroup.datestr_to_date(result['lastUpdate']),
            )
            debug(f"Got result {result}")
            results.add(result)

        # All done!
        return results

    def _search_by_target(
        self,
        target: str,
        target_type: Literal['CERTIFICATE', 'USER', 'WORKGROUP'],
    ) -> SearchByResults:
        """Search for workgroups by target.

        :param target_type: The type of thing to search for.  Either a
            certificate, a user, or a workgroup.

        :param target: The thing to search for.

        :returns: A collection of partial workgroups.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).  Or, you searched for a target that
            does not exist.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises ValueError: The search string is empty.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        debug(f"In _search_by_target for {target_type} {target}")

        # Make sure the search string is not empty, and does not start with an
        # asterisk.
        if len(target) == 0:
            raise ValueError('Search string is empty')

        # Make the request for the Workgroup.
        get_url = self._url(
            query_dict={
                'type': target_type,
                'id': target,
            },
        )
        debug(f"Doing GET of {get_url}")
        response = self.client.session.get(
            get_url,
        )

        # Catch a number of bad errors.
        if response.status_code in (400, 500):
            error(f"Upstream API error: {response.text}")
            raise ChildProcessError(response.text)
        if response.status_code in (401, 403):
            warning(f"Permission error on search for {target_type} {target}")
            raise PermissionError(f"{target_type} {target}")

        # Decode the JSON, and get our search results
        debug('Got a response!')
        response_json = response.json()
        print(response_json)

        # We get a dict list of members and a list of administrators
        result_sets: dict[Literal['members', 'administrators'], set] = {
            'members': set(),
            'administrators': set(),
        }
        for (result_set_name, result_set) in result_sets.items():
            for result_json in response_json[result_set_name]:
                result = PartialWorkgroup(
                    name=result_json['name'],
                    description=('' if 'description' not in result_json else result_json['description']),
                    last_update=Workgroup.datestr_to_date(result_json['lastUpdate']),
                )
                result_set.add(result)

        results = SearchByResults(
            is_member=frozenset(result_sets['members']),
            is_administrator=frozenset(result_sets['administrators']),
        )

        # All done!
        return results

    def search_by_user(
        self,
        sunetid: str,
    ) -> SearchByResults:
        """Search for workgroups containing the specified SUNetID.

        A workgroup will be included in the result if the specified SUNetID is
        a member or an administrator (or both).

        .. note::
            If the user is a stem administrator, then the user automatically
            becomes an administrator of every workgroup in that stem, and all
            those workgroups will be included in the results.

        :param sunetid: The SUNetID to search for.

            .. note::
                Wildcards are not allowed.

        :returns: A set of partial workgroups where the person is a member, and
            a set of partial workgroups where the person is an administrator.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).  Or, you searched for a SUNetID that
            does not exist.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises ValueError: The search string is empty.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        return self._search_by_target(
            target_type='USER',
            target=sunetid,
        )

    def search_by_certificate(
        self,
        certificate: str,
    ) -> SearchByResults:
        """Search for workgroups containing the specified certificate.

        A workgroup will be included in the result if the specified certificate
        is an administrator of the workgroup, or is a stem administrator.

        .. note::
            If the certificate is a stem administrator, then the certificate
            automatically becomes an administrator of every workgroup in that
            stem, and all those workgroups will be included in the results.

        :param certificate: The "common name" of the certificate to search for.
            The common name is also known as the "CN" attribute, and is part of
            the certificate's subject.

            .. note::
                Wildcards are not allowed.

        :returns: A set of partial workgroups where the certificate is a
            member, and a set of partial workgroups where the person is an
            administrator.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).  Or, you searched for a
            certificate that does not exist.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises ValueError: The search string is empty.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        return self._search_by_target(
            target_type='CERTIFICATE',
            target=certificate,
        )

    def search_by_workgroup(
        self,
        workgroup: str,
    ) -> SearchByResults:
        """Search for workgroups containing the specified workgroup.

        A workgroup will be included in the result if the specified workgroup
        is nested in the workgroup's members or administrators list.

        For example, say you are searching for workgroup ``abc:def``.  If
        workgroup ``abc:123`` has ``abc:def`` nested in the members or
        administrators lists (or both), then workgroup ``abc:123`` will be
        included in the results.

        .. note::
            If the workgroup is a stem administrator, then the workgroup
            automatically becomes an administrator of every workgroup in that
            stem, and all those workgroups will be included in the results.

        :param workgroup: The workgroup to search for.

            .. note::
                This must be a fully-qualified workgroup name.  For example,
                ``research-computing:sysadmins``.  Wildcards are not allowed.

        :returns: A set of partial workgroups where the workgroup is nested as
            a member, and a set of partial workgroups where the workgroup is
            nested as an administrator.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).  Or, you searched for a workgroup
            that does not exist.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises ValueError: The search string is empty.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        return self._search_by_target(
            target_type='WORKGROUP',
            target=workgroup,
        )

    def clear_cache(
        self,
    ) -> None:
        """Clear cache of workgroups.

        This clears the cache of workgroups.

        As mentioned in the class docs, visited workgroups are cached locally,
        for speed and to reduce load on the Workgroup API.  In long-running
        programs, this can be a problem.  To assist, this method clears the
        cache of this specific Workgroup client.

        .. note::
            If you are looking to see changes in a specific workgroup, you
            should not use this method.  Instead, you should call
            :meth:`~Workgroup.refresh` on the workgroup of interest.

        .. danger::
            If you are holding a reference to an existing :class:`Workgroup`,
            or to one of the the Workgroup's :class:`WorkgroupMembership`
            or :class:`WorkgroupMembershipContainer`, clearing the cache does
            not invalidate those references!

            This method should not be called unless you know what you are
            doing.
        """
        debug('in clear_cache')
        self._cache.clear()

    def _url(
        self,
        fragment: pathlib.PurePosixPath | str | None = None,
        query_dict: Mapping[str, str] = dict(),
    ) -> str:
        """Return a URL for a specific Workgroups API call.

        :param fragment: An optional path or string, to append to the base URL.

        :param query_dict: A dict of key-value entries to make into the URL's
            query string.  May be empty.
        """

        # We can't use urllib.parse.urljoin, because it interprets the colon in
        # the workgroup name.  So, extract the path and use pathlib.
        url_components = urllib.parse.urlparse(self.client.urls['workgroup'])

        url_path = pathlib.PurePosixPath(url_components.path)
        if fragment is None:
            combined_path = url_path
        elif isinstance(fragment, pathlib.PurePosixPath):
            combined_path = url_path / fragment
        else:
            combined_path = url_path / pathlib.PurePosixPath(fragment)

        # If we've got a query dict, convert it to UTF-8 bytes and assemble.
        query_str = ''
        if len(query_dict) > 0:
            query_str = urllib.parse.urlencode(
                query=query_dict,
                encoding='utf-8',
                quote_via=urllib.parse.quote,
            )

        # Reassemble the URL, also inserting a query string (if we have one).
        return urllib.parse.urlunparse((
            url_components.scheme,
            url_components.netloc,
            str(combined_path),
            '',
            query_str,
            ''
        ))
