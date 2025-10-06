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
from collections.abc import Mapping
import dataclasses
import datetime
import logging
import pathlib
import re
import requests
from typing import Any, Literal, TYPE_CHECKING
import weakref
import zoneinfo

# Finally, do local imports
from stanford.mais.workgroup.properties import *
from stanford.mais.workgroup.member import *

# There are some needed type annotations where, if we imported them now, we
# would make an import loop.  So, only import them when type-checking.
if TYPE_CHECKING:
    from stanford.mais.workgroup import WorkgroupClient

# Set up logging

logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error

__all__ = (
    'Workgroup',
    'WorkgroupDeleted',
    'WorkgroupFilter',
    'WorkgroupVisibility',
    'PrivgroupContents',
    'PrivgroupEntry',
)


# First, some Privgroup-related stuff


@dataclasses.dataclass(frozen=True)
class PrivgroupEntry:
    sunetid: str
    """The person's SUNetID.
    """

    name: str
    """The person's name, in 'Last, First' format.
    """

    last_update: datetime.date
    """The date when the person became part of the privgroup.
    """

    @classmethod
    def from_json(
        cls,
        json: dict[str, Any],
    ) -> PrivgroupEntry:
        """Make a privgroup entry from a Workgroups API JSON object.
        """

        # Make sure our keys are in the dict
        if 'name' not in json:
            raise KeyError('name')
        if 'id' not in json:
            raise KeyError('id')
        if 'lastUpdate' not in json:
            raise KeyError('lastUpdate')

        # Make the class
        return cls(
            sunetid=json['id'],
            name=json['name'].rstrip(),
            last_update=Workgroup.datestr_to_date(json['lastUpdate']),
        )


@dataclasses.dataclass(frozen=True)
class PrivgroupContents:
    members: set[PrivgroupEntry]
    administrators: set[PrivgroupEntry]


# Next, Workgroup-related exceptions:


class WorkgroupDeleted(KeyError):
    """Workgroup used to exist, but has been deleted.

    This exception is raised whenever a workgroup is "inactive", which means
    that it used to exist, but has been deleted.  Constrast that with a
    workgroup never having existed, which triggers the raise of a KeyError.

    This exception exists for folks who care if a workgroup used to exist:
    Folks who don't care can simply catch KeyError, which will work because
    this is a subclass of KeyError.
    """
    pass


# Now, on to the Workgroup!


class Workgroup:
    """A Stanford Workgroup.
    """

    # Methods are grouped by their position in the CRUD acronym:
    # C: Create
    # R: Read/Report
    # U: Update
    # D: Delete

    #
    # "C" methods
    #

    @classmethod
    def create(
        cls,
        client: WorkgroupClient,
        name: str,
        description: str,
        filter: WorkgroupFilter = WorkgroupFilter.NONE,
        privgroup: bool = True,
        reusable: bool = True,
        visibility: WorkgroupVisibility = WorkgroupVisibility.STANFORD,
    ) -> Workgroup:
        """Create a new workgroup.

        Your client certificate must be a stem owner in order to create
        workgroups in a given stem.

        Once created, a workgroup will have no members, and two
        administrators:

        * *The stem-owner group*.  For example, workgroup ``abc:def`` will
          have ``workgroup:abc-owners`` nested as an administrator.
          **This cannot be changed**.

        * *Your client certificate*.  Even though your client certificate
          is already a stem owner—and therefore an administrator—it will be
          explicitly added as an administrator.
          You *are allowed* to remove your client certificate from the list
          of workgroup administrators.  To do so, use code like this:

        .. code-block:: python

            wclient = WorkgroupClient(...)
            workgroup = Workgroup.create(client=wclient, ...)
            workgroup.administrators.certificates.remove(CLIENT_CERT_CN)

        :param client: A :class:`WorkgroupClient`.

        :param name: The fully-qualified workgroup name.  Required.  For
            example, to create a workgroup named `abc` in stem `school`, use
            name `school:abc`.  The name portion is limited to 81 characters,
            which may contain only lowercase letters, numbers, hyphens, and
            underscores.  The name portion must start with a letter or number.

        :param description: The workgroup description.  It must contain at
            least one character.  Limited to 255 characters from the ISO 8859-1
            ("Latin 1") character set.

        :param filter: Optional.  See :meth:`filter`.  Defaults to `NONE`.

        :param privgroup: Optional.  See :meth:`privgroup`.  Defaults to
            `True`.

        :param reusable: Optional.  See :meth:`reusable`.  Defaults to `True`.

        :param visibility: Optional.  See :meth:`visibility`.  Defaults to
            `STANFORD`.

        :returns: An instance of the newly-created workgroup.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raise IndexError: The proposed workgroup name or description is too
            short or too long.

        :raise ValueError: The proposed workgroup name or description has
            invalid characters.

        :raise KeyError:
            A workgroup with this name already exists.

        :raises WorkgroupDeleted:
            The proposed workgroup name was already used for a
            workgroup, and that workgroup has since been deleted.

            .. note::
                Deleted workgroups are not really deleted, just hidden.
                Stem owners can restore 'deleted' workgroups through the
                Workgroup Manager web site.

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises NotImplementedError: Received an unexpected HTTP response code.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        debug(f"In create for name '{name}'")

        # Check the length of the workgroup name.
        if len(name) > 81:
            error(f"Proposed name '{name}' is too long")
            raise IndexError('name')

        # Check if the name is invalid.
        if re.fullmatch(
            r'[a-z0-9][a-z0-9_-]*:[a-z0-9][a-z0-9_-]*',
            name,
        ) is None:
            error(f"Proposed name '{name}' is not valid")
            raise ValueError('name')

        # Check the length of the description.
        if len(description) == 0:
            error('Proposed description is too short')
            raise IndexError('description')
        if len(description) > 255:
            error(f"Proposed description is too long")
            raise IndexError('description')

        # Check if the description has nonprintable characters or is non-Latin1
        try:
            description.encode('latin1')
        except UnicodeError:
            error('Proposed description is not encodable in ISO 8859-1')
            raise ValueError('description')
        if not description.isprintable():
            error(f"Proposed description has non-printable characters")
            raise ValueError('description')

        # Get the Requests session
        session = client.client.session

        # Make the Workgroup.
        post_url = client._url(
            fragment=name,
        )
        debug(f"Filter is '{filter}' — Visibility is '{visibility}'")
        debug(f"Running POST to {post_url} to create workgroup")
        response = client.client.session.post(
            post_url,
            json={
                'description': description,
                'filter': str(filter),
                'privgroup': ('TRUE' if privgroup is True else 'FALSE'),
                'reusable': ('TRUE' if reusable is True else 'FALSE'),
                'visibility': str(visibility),
            },
        )

        # Catch an inactive workgroup.
        match response.status_code:
            case 400:
                response_json = None
                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError:
                    pass

                # Did our workgroup go inactive out from under us?
                if (
                    response_json is not None and
                    response_json['notification'] == 'Workgroup is inactive'
                ):
                    warning(f"Workgroup {name} used to exist but has been deleted")
                    raise WorkgroupDeleted(name)
                else:
                    # We have a generic 400 error
                    raise ChildProcessError(response.text)
            case 500:
                error(f"Upstream API error: {response.text}")
                raise ChildProcessError(response.text)
            case 401 | 403:
                warning(f"Permission error on create workgroup {name}")
                raise PermissionError(response.text)
            case 409: # Catch an already-existing workgroup
                warning(f"Workgroup {name} already exists")
                raise KeyError(name)
            case _ if response.status_code != 201:
                raise NotImplementedError(response.text)

        # Decode the JSON, and send to make the instance
        debug(f"Got back a response!")
        response_json = response.json()
        result = cls(
            client=client,
            from_json=response_json,
        )

        # Put our new workgroup into the cache, and return
        client._cache[name] = weakref.ref(result)
        return result

    @classmethod
    def get(
        cls,
        client: WorkgroupClient,
        name: str,
    ) -> Workgroup:
        """Fetch a Workgroup.

        Fetch an existing Workgroup using the MaIS Workgroup API, and return
        the corresponding :class:`Workgroup` instance.  If the instance already
        exists in the cache, the cached instance will be returned.

        .. note::
            Use the :attr:`last_refresh` property to see if your instance is
            too old, and the :meth:`refresh` method to refresh it.

        .. warning::
            If the workgroup's visibility is set to `PRIVATE`, and your client
            certificate is not an administrator of the workgroup (either
            directly, or via stem ownership), then…

            * The :attr:`can_see_membership` property will be ``False``;

            * The sets of members and administrators will be empty; and

            * All attempts to access the privgroup list or make changes will
              return a :class:`PermissionError`.

        :param client: A :class:`WorkgroupClient` representing our API endpoint.

        :param name: The name of the workgroup to fetch.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned), or you did not provide a workgroup
            name.

        :raises KeyError: The workgroup does not exist, and has never existed.

        :raises WorkgroupDeleted: The workgroup used to exist, but was deleted.

        :raises PermissionError: You did not use a valid certificate.

        :raises NotImplementedError: Received an unexpected HTTP response code.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        # Lowercase the name before we continue
        name = name.lower()
        debug(f"In get for Workgroup name {name}")

        # Check if the Workgroup is in the cache
        if name in client._cache:
            result = client._cache[name]()
            if result is not None:
                debug(f"Returning Workgroup {name} from cache")
                return result
            else:
                debug(f"{name} expired in cache.  Re-fetching…")

        # Make the request for the Workgroup.
        get_url = client._url(
            fragment=name,
        )
        debug(f"Doing GET of {get_url}")
        response = client.client.session.get(
            get_url,
        )

        # Catch an inactive workgroup.
        match response.status_code:
            case 400:
                response_json = None
                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError:
                    pass

                # Did our workgroup go inactive out from under us?
                if (
                    response_json is not None and
                    response_json['notification'] == 'Workgroup is inactive'
                ):
                    warning(f"Workgroup {name} has been deleted")
                    raise WorkgroupDeleted(name)
                else:
                    # We have a generic 400 error
                    raise ChildProcessError(response.text)
            case 500:
                error(f"Upstream API error: {response.text}")
                raise ChildProcessError(response.text)
            case 401 | 403:
                warning(f"Permission error on get {name}")
                raise PermissionError(response.text)
            case 404:
                warning(f"Workgroup {name} not found")
                raise KeyError(name)
            case _ if response.status_code != 200:
                raise NotImplementedError(response.text)

        # Decode the JSON, and send to make the instance
        debug('Got a response!')
        response_json = response.json()
        result = cls(
            client=client,
            from_json=response_json,
        )

        # Put into the cache and return!
        client._cache[name] = weakref.ref(result)
        return result

    def refresh(self) -> None:
        """Refresh an existing Workgroup instance.

        Make a query to the Workgroups API to update this instance.  This will
        refresh all properties, including membership.  The only thing
        guaranteed *not* to change is the workgroup's name.

        .. note::
            It is possible that your client certificate gained administrator
            access between this instance's creation, and now.  It is also
            possible that your client certificate *lost* administrator access.

        .. danger::
            It is also possible that someone else has deleted the workgroup.
            If that happens, the :attr:`deleted` property will be set and a
            :class:`WorkgroupDeleted` exception will be raised.

        .. warning::
            If your client certificate is not an administrator of the
            workgroup (either directly, or via stem ownership), then…

            * The :attr:`can_see_membership` property will be ``False``;

            * The sets of members and administrators will be empty; and

            * All attempts to access the privgroup list or make changes will return
              a :class:`PermissionError`.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises WorkgroupDeleted: The workgroup has been deleted.

        :raises NotImplementedError: Received an unexpected HTTP response code.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        debug(f"In refresh for Workgroup name {self.name}")
        if self.deleted:
            raise EOFError('Workgroup has been deleted')

        # Make the request for the Workgroup.
        get_url = self.client._url(
            fragment=self.name,
        )
        debug(f"Doing GET of {get_url}")
        response = self.client.client.session.get(
            get_url,
        )

        # Hand off the change for processing
        return self._handle_refresh(response)

    def _mark_deleted(self) -> None:
        """Mark an instance as deleted

        When a workgroup is deleted, this updates various fields in the
        Workgroup instance.  This could happen because we intentionally deleted
        the workgroup, or the workgroup could have been deleted by someone
        else, after the instance was created.
        """

        # We will leave all existing properties alone, but we will force
        # the members and administrators sets to become empty.
        self._members.update_from_upstream(list())
        self._administrators.update_from_upstream(list())

        # Update last-refresh & mark the instance as deleted
        self._last_refresh = datetime.datetime.now(tz=datetime.timezone.utc)
        self._deleted = True

        # All done!

    def _handle_refresh(
        self,
        response: requests.Response,
    ) -> None:
        """Process the response from a refresh.

        This method takes the Requests Response that is generated by doing a
        refresh, and updates this instance appropriately.

        Potentially, *any* part of this instance can change, except for the
        workgroup's name.  That workgroup may even have been deleted!  For this
        reason, this method takes the entire Response, not just the JSON part.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises WorkgroupDeleted: The workgroup has been deleted.

        :raises NotImplementedError: Received an unexpected HTTP response code.
        """

        # Did our change go through?
        if response.status_code == 200:
            # It worked!  Send it through for normal processing.
            debug('Got a response!')
            response_json = response.json()
            self._from_json(response_json)

        # Catch various errors
        match response.status_code:
            case 400:
                response_json = None
                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError:
                    pass

                # Did our workgroup go inactive out from under us?
                if (
                    response_json is not None and
                    response_json['notification'] == 'Workgroup is inactive'
                ):
                    error(f"Already-instanced workgroup {self.name} has been deleted")
                    self._mark_deleted()
                    raise WorkgroupDeleted(self.name)
                else:
                    # We have a generic 400 error
                    raise ChildProcessError(response.text)
            case 500:
                error(f"Upstream API error: {response.text}")
                raise ChildProcessError(response.text)
            case 401 | 403:
                warning(f"Permission error on get {self.name}")
                raise PermissionError(response.text)
            case 404:
                warning(f"Workgroup {self.name} not found")
                raise KeyError(self.name)
            case _ if response.status_code != 200:
                raise NotImplementedError(response.text)

        # All done!
        return None

    # Actually set up a new instance.
    def __init__(
        self,
        **kwargs,
    ) -> None:
        debug('In __init__')
        # Error out if we didn't get our expected data.
        if 'from_json' not in kwargs or 'client' not in kwargs:
            raise NotImplementedError('Do not instantiate Workgroups directly.')
        client: 'WorkgroupClient' = kwargs['client']
        response_json: Mapping[str, Any] = kwargs['from_json']

        # We know that this workgroup exists right now.
        self._deleted = False

        # Set a couple of properties that will never change.
        self._client = client
        self._name = response_json['name']

        # Make empty containers for members and administrators
        self._members: WorkgroupMembership = WorkgroupMembership(
            workgroup=self,
            collection_type='members',
        )
        self._administrators: WorkgroupMembership = WorkgroupMembership(
            workgroup=self,
            collection_type='administrators',
        )

        # Process the remaining properties
        self._from_json(response_json)

    def _from_json(
        self,
        response_json: Mapping[str, Any],
    ) -> None:
        """Process the JSON from a Workgroups API "Get Workgroup" call.

        This method updates our instance with all of the data received from the
        Workgroups API.  It is meant to be called on instance creation, and on
        instance refresh.

        .. note::
            This method does not handle setting the workgroup name.  That never
            changes throughout a workgroup's life.

        :param response_json: The dict containing the decoded Workgroup JSON.
        """
        debug(f"In _from_json for workgroup {self.name}")

        # The description is the only field that might not be present.
        if 'description' in response_json:
            self._description = response_json['description']
        else:
            self._description = ''
        debug(f"Name is {self._name}, description is {len(self._description)} characters")

        # Set our boolean properties
        if response_json['privgroup'] == 'TRUE':
            debug('Privgroup is on')
            self._privgroup = True
        else:
            debug('Privgroup is OFF')
            self._privgroup = False
        if response_json['reusable'] == 'TRUE':
            debug('Reusable is on')
            self._reusable = True
        else:
            debug('Reusable is OFF')
            self._reusable = False

        # Set our enum properties
        self._visibility = WorkgroupVisibility.from_str(
            response_json['visibility']
        )
        self._filter = WorkgroupFilter.from_str(
            response_json['filter']
        )
        debug(f"Visibility is {self._visibility}s — Privgroup is {self._privgroup}s")

        # Set the last-updated date
        self._last_update = self.datestr_to_date(response_json['lastUpdate'])

        # Update the members and administrators containers.
        debug('Building memberships')
        self._members.update_from_upstream(
            response_json=response_json['members'],
        )
        self._administrators.update_from_upstream(
            response_json=response_json['administrators'],
        )

        # Can we see the workgroups members and administrators?
        # The `can_see_membership` property explains the rules, but there's a
        # sneaky workground we can use:
        # Every workgroup has the stem-owner group as administrators.  So,
        # check if we can see *any* administrators.
        self._can_see_membership = (True if len(self._administrators) > 0 else False)

        # Update our last-refreshed time, and we're done!
        self._last_refresh = datetime.datetime.now(tz=datetime.timezone.utc)
        debug('Instance construction/update complete!')
        return None

    #
    # "R" methods.
    #

    # Most of the instance is accessed via properties.
    # We start with those that don't deal with collections of things.

    @property
    def client(self) -> WorkgroupClient:
        """Return the :class:`WorkgroupClient` that was used to fetch this
        :class:`Workgroup`.
        """
        return self._client

    @property
    def deleted(self) -> bool:
        """Is the workgroup deleted?

        If :meth:`delete` is called on the workgroup, this property is set to
        ``True``, and all methods & properties will raise an :class:`EOFError`.
        The exception are this method, and :attr:`client`.

        .. note::
            This property may also become ``True`` if you called
            :meth:`refresh` on the instance, and the refresh reveals that the
            workgroup has been deleted.
        """
        return self._deleted

    @property
    def name(self) -> str:
        """The fully-qualified name of the workgroup.

        This may not be changed after the workgroup is created.

        .. note::
            Since workgroups are never actually "deleted", just hidden, the
            name remains accessible even after deletion.
        """
        return self._name

    @property
    def last_refresh(self) -> datetime.datetime:
        """When the instance was last refreshed.

        This is set to the (aware) datetime when the instance was last
        refreshed from the Workgroup API.  The following actions can trigger a
        refresh:

        * Calling :meth:`create` or :meth:`get`.

        * Calling :meth:`refresh`.

        * Changing any property of the workgroup.

        .. note::
           If :meth:`delete` is called to delete the workgroup, this will
           return the datetime when the workgroup was deleted.
        """
        return self._last_refresh

    @property
    def description(self) -> str:
        """The workgroup description.

        This is a property: Use as a value to get the current description; call
        with a string to change the current setting.

        .. warning::
            Changing a workgroup property triggers a refresh of the entire
            workgroup.  See the documentation for :meth:`refresh`; all of those
            warnings apply here.

        :param str value: The new description.  The maximum length is 255
            characters.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.

        :raise IndexError: The new description is too long.

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._description

    @property
    def last_update(self) -> datetime.date:
        """The date when the workgroup was last updated.

        When the workgroup's properties, members, or administrators are
        updated, this datestamp resets.

        .. warning::
            This date is in the Stanford-local time zone.  Remember to take
            this into account when doing comparisons.

        .. note::
            Why is it a date, instead of a datetime?  Because that is what the
            Workgroup API provides.

        .. danger::
            Privgroup member and administrator changes do not reset the
            last_update datestamp.  This is a "last updated" for the workgroup,
            not the privgroup!

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._last_update

    @property
    def filter(self) -> WorkgroupFilter:
        """The workgroup filter.

        This controls the effective membership of the workgroup.  See the
        definition of
        :class:`~stanford.mais.workgroup.properties.WorkgroupFilter` for more
        information on how Workgroup filters take the real membership (which
        you see through this API) and filter it to provude an effective
        membership (which others see).

        This is a property: Use as a value to get the current description; call
        with a :class:`~stanford.mais.workgroup.properties.WorkgroupFilter` (or
        equivalent string) to change the current setting.

        .. warning::
            Changing a workgroup property triggers a refresh of the entire
            workgroup.  See the documentation for :meth:`refresh`; all of those
            warnings apply here.

        :param value:
            The new filter.  This may either be a
            :class:`~stanford.mais.workgroup.properties.WorkgroupFilter`,
            or a string that parses cleanly into a
            :class:`~stanford.mais.workgroup.properties.WorkgroupFilter`.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.

        :raises ValueError: The value provided does not match an enum value.
            This may only be thrown when providing a :class:`str` for `value`.

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._filter

    @property
    def privgroup(self) -> bool:
        """Does the workgroup have an associated privgroup?

        A 'privgroup' is a flattened list of workgroup members and
        administrators, with certificates removed, nested workgroups flattened,
        and filters applied.

        As described in :meth:`filter`,
        workgroups have a *real* list of members (which is accessed &
        maintained by this API) and an *effective* list of members (after the
        workgroup membership is flattened and filter applied).

        If `privgroup` is ``True``, then the flattened and filtered list
        of workgroup members and administrators will be made available to
        downstream systems like LDAP.  If ``False``, then the workgroup
        may only be used within Workgroup Manager (for example, it can be
        nested in other workgroups).

        .. warning::
            If you disable privgroup on a workgroup and then nest it into
            another workgroup, this workgroup's members will **not** appear in
            the privgroup of the nested workgroup.

        .. note::
            This property cannot be changed through the Workgroup Manager web
            site, only through the API.

        This is a property: Use as a value to get the current description; call
        with a :class:`bool` to change the current setting.

        .. warning::
            Changing a workgroup property triggers a refresh of the entire
            workgroup.  See the documentation for :meth:`refresh`; all of those
            warnings apply here.

        :param bool value: The new privgroup setting.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.

        :raises TypeError: `value` was not a :class:`bool`.

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._privgroup

    @property
    def reusable(self) -> bool:
        """May the workgroup be nested outside of its stem?

        If `reusable` is ``True``, then this workgroup may only be nested
        within other workgroups of the same stem.  Otherwise, this workgroup
        may be nested in any workgroup.

        "nesting" means including the *effective* membership of one workgroup
        in another.  See :meth:`filter` for
        information on real vs. effective workgroup membership.

        Use as a property to get the current reusable setting; call with
        parameters to change the current reusable setting.

        .. warning::
            Changing this setting will **not** affect existing nesting
            relationships.  You can view existing nesting relationships in
            Workgroup Manager.

        This is a property: Use as a value to get the current description; call
        with a :class:`bool` to change the current setting.

        .. warning::
            Changing a workgroup property triggers a refresh of the entire
            workgroup.  See the documentation for :meth:`refresh`; all of those
            warnings apply here.

        :param bool value: The new reusable setting.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.

        :raises TypeError: `value` was not a :class:`bool`.

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._reusable

    @property
    def visibility(self) -> WorkgroupVisibility:
        """Is the workgroup's membership visible to others?

        See :class:`~stanford.mais.workgroup.properties.WorkgroupVisibility`
        for an explanation of the different workgroup visibility options.

        Use as a property to get the current visibility setting; call with
        parameters to change the current filter setting.

        .. danger::
            Setting this to ``PRIVATE`` can cause unexpected and unusual issues
            in downstream applications.

        This is a property: Use as a value to get the current description; call
        with a :class:`~stanford.mais.workgroup.properties.WorkgroupVisibility`
        (or equivalent string) to change the current setting.

        .. warning::
            Changing a workgroup property triggers a refresh of the entire
            workgroup.  See the documentation for :meth:`refresh`; all of those
            warnings apply here.

        :param value:
            The new visibility.  This may either be a
            :class:`~stanford.mais.workgroup.properties.WorkgroupVisibility`,
            or a string that parses cleanly into a
            :class:`~stanford.mais.workgroup.properties.WorkgroupVisibility`.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.

        :raises ValueError: The value provided does not match an enum value.

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._visibility

    @property
    def can_see_membership(self) -> bool:
        """Can we see the workgroup's members and administrators?

        See :attr:`visibility` for an
        explanation of workgroup visibility.

        If this workgroup's visibility is `STANFORD`, then we can see the
        members and administrators of the workgroup.

        If this workgroup's visibility is `PRIVATE`, then the client
        certificate must be a workgroup administrator.  If yes, then we can see
        the members and administrators of the workgroup.

        If this workgroup's visibility is `PRIVATE`, and the client certificate
        is **not** a workgroup administrator, then we *cannot* see the members
        and administrators of a workgroup:  The sets will appear empty.

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._can_see_membership

    # Next, we have the different containers.

    @property
    def members(self) -> WorkgroupMembership:
        """Access the sets of workgroup members.

        .. note::
            This is the *real* set of members, not the *effective* membership.
            Refer to
            :class:`~stanford.mais.workgroup.properties.WorkgroupFilter` for
            more information.

        See :class:`~stanford.mais.workgroup.member.WorkgroupMembership` for
        information on how access the sets of member people (SUNetIDs),
        workgroups (fully-qualified names), and certificates (client
        certificate subject common names).

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._members

    @property
    def administrators(self) -> WorkgroupMembership:
        """Access the sets of workgroup administrators.

        .. note::
            There is no difference between the *real* and *effective* set of
            workgroup administrators.  Anyone or anything included here has
            administrative power over the workgroup, regardless of filter.  The
            one exception is when a nested workgroup has a filter set, in which
            case the filter applies to that workgroup's membership only.

            Refer to
            :class:`~stanford.mais.workgroup.properties.WorkgroupFilter` for
            more information on filters.

        See :class:`~stanford.mais.workgroup.member.WorkgroupMembership` for
        information on how access the sets of administrator people (SUNetIDs),
        workgroups (fully-qualified names), and certificates (client
        certificate subject common names).

        :raises EOFError: The workgroup has been deleted.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        return self._administrators

    def __repr__(self) -> str:
        if self.deleted:
            return "Workgroup(deleted)"
        
        # This will be the bits we assemble at the end
        pieces: list[str] = list()

        # Start with the name
        pieces.append(f"name=\"{self.name}\"")

        # For the description, we need to escape double-quotes
        escaped_description = self.description.replace('"', '\\"')
        pieces.append(f"description=\"{escaped_description}\"")

        # These properties need no additional handling
        pieces.append(f"visibility={self.visibility}")
        pieces.append(f"reusable={self.reusable}")
        pieces.append(f"privgroup={self.privgroup}")
        pieces.append(f"filter={self.filter}")
        pieces.append(f"members={self.members}")
        pieces.append(f"administrators={self.administrators}")
        pieces.append(f"last_update={self.last_update}")

        # Put it all together
        return 'Workgroup(' + ','.join(pieces) + ')'

    def get_privgroup(self) -> PrivgroupContents:
        """Generate the current privilege group listing.

        A privgroup is a list of actual people (no workgroups or certificates).
        A workgroup has two privgroups: One for members and one for
        administrators.

        For the privgroup of members, start with an empty list, and do the
        following:

        1. Add all of this workgroup's members that are people.
        2. For each of this workgroup's members that are workgroups, *if the
           nested workgroup's privgroup property is enabled*, then calculate
           the nested workgroup's privgroup (members only), and add those
           people to this list.
        3. Remove all duplicates
        4. Remove all people who do not meet this workgroup's filter.

        For the privgroup of administrators, start with an empty list, and do
        the following:

        1. Add all of this workgroup's administrators that are people.
        2. For each of this workgroup's administrators that are workgroups,
           *if the nested workgroup's privgroup property is enabled*, then
           calculate the nested workgroup's privgroup (**members only**), and
           add those people to this list.
        3. Remove all duplicates
        4. Remove all people who do not meet this workgroup's filter.

        Since the privgroup's contents potentially depend on ths membership of
        other workgroups, the workgroup's 

        .. note::
            To get the privgroup for a workgroup, your client certificate must
            be able to see the membership of this workgroup, otherwise a
            `PermissionError` will be raised.  See :meth:`can_see_membership`.

        .. warning::
            It is possible that your client certificate gained administrator
            access between this instance's creation, and now.  If you think
            that happened, call :meth:`refresh` before calling this method.

            It is also possible that your client certificate *lost*
            administrator access, or that a workgroup was made private.  In
            that case, this method will return a PermissionError even though
            :meth:`can_see_membership` returns `True`.

        .. danger::
            It is also possible that someone else has deleted the workgroup.
            If that happens, the :attr:`deleted` property will be set and a
            :class:`WorkgroupDeleted` exception will be raised.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises WorkgroupDeleted: The workgroup has been deleted.

        :raises NotImplementedError: Received an unexpected HTTP response code.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        debug(f"In get_privgroup for {self.name}")

        # If we cannot see a workgroup's membership, then we won't be able to
        # see the privgroup, so don't bother making the API call.
        # NOTE: We still catch 401/403 errors, though, just in case permissions
        # changed since we first fetched the workgroup.
        if not self.can_see_membership:
            raise PermissionError()

        # Our URL includes the fully-qualified workgroup name, plus `privgroup`
        url_fragment = (
            pathlib.PurePosixPath(self.name) /
            pathlib.PurePosixPath('privgroup')
        )

        response = self.client.client.session.get(
            self.client._url(
                fragment=url_fragment,
            ),
        )

        # Catch various errors
        match response.status_code:
            case 400:
                response_json = None
                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError:
                    pass

                # Did our workgroup go inactive out from under us?
                if (
                    response_json is not None and
                    response_json['notification'] == 'Workgroup is inactive'
                ):
                    error(f"Already-instanced workgroup {self.name} has been deleted")
                    self._mark_deleted()
                    raise WorkgroupDeleted(self.name)
                else:
                    # We have a generic 400 error
                    raise ChildProcessError(response.text)
            case 500:
                error(f"Upstream API error: {response.text}")
                raise ChildProcessError(response.text)
            case 401 | 403:
                warning(f"Permission error on get {self.name}")
                raise PermissionError(response.text)
            case _ if response.status_code != 200:
                raise NotImplementedError(response.text)

        # Did we get a response?
        debug('Got a response!')

        # Get results, and make containers for holding results
        results = response.json()
        administrators: set[PrivgroupEntry] = set()
        members: set[PrivgroupEntry] = set()

        # Process the results and return
        for administrator in results['administrators']:
            administrators.add(PrivgroupEntry.from_json(administrator))
        for member in results['members']:
            members.add(PrivgroupEntry.from_json(member))

        debug(f"Returning {len(administrators)} admins and {len(members)} members")
        return PrivgroupContents(
            members=members,
            administrators=administrators,
        )

    #
    # "U" methods.
    #

    # Handle the last-updated date in its own call.

    def _reset_last_update(self) -> None:
        """Reset the "last-updated" date to today.

        This method is called by anything that updates any part of the
        workgroup.  It's a separate method from :meth:`update` because this
        can also be called by workgroup-membership and integration classes.
        """
        debug(f"In _reset_last_update for {self.name}")
        now_utc = datetime.datetime.now(tz=datetime.timezone.utc)
        now_stanford = now_utc.astimezone(tz=zoneinfo.ZoneInfo(key='America/Los_Angeles'))
        self._last_update = now_stanford.date()

    # The non-container properties are all updated with the same type of call.
    # So, make a method to implement that call.

    def _update(
        self,
        name: Literal[
            'description',
            'filter',
            'privgroup',
            'reusable',
            'visibility',
        ],
        value: str,
    ) -> None:
        """Update a workgroup's property.

        This is used by the property setters in this class.  It sends the
        requested change to the Workgroup API.

        The change might fail, due to a permission error or due to the
        workgroup being deleted from under us.  Or the change might succeed,
        and the response from the Workgroup API will be the full workgroup
        record (which includes our just-made change).  Either way, that sounds
        a lot like a refresh, so send the response to the refresh-handling
        code!

        :param name: The name of the property to change.

        :param value: The new value for the property.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises NotImplementedError: Received an unexpected HTTP response code.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')

        # Make the request for the Workgroup.
        response = self.client.client.session.put(
            self.client._url(
                fragment=self.name
            ),
            json={
                name: value,
            },
        )

        # At this point, it's as if we did a refresh, so send off to the
        # refresh-handling code.
        return self._handle_refresh(response)

    # Setters for properties defined in the "R" section.

    # NOTE: These setters all have the "no-redef" and "attr-defined" checks
    # ignored in MyPy.  This is because MyPy can't handle property setters
    # being anything other than immediately after the corresponding getter.
    # See https://github.com/python/mypy/issues/1465

    @description.setter  # type: ignore[no-redef,attr-defined]
    def description(
        self,
        value: str,
    ) -> None:
        """Set the new description.

        See :py:property:`description` for information on this property.
        You must be a workgroup administrator to use this property setter.

        :raise IndexError: The proposed description is too short or too long.

        :raise ValueError: The proposed description has invalid characters.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        if len(value) == 0:
            error('Proposed description is too short')
            raise IndexError('description')
        if len(value) > 255:
            raise IndexError(self.name)

        # Check if the description has nonprintable characters or is non-ASCII
        try:
            value.encode('latin1')
        except UnicodeError:
            error('Proposed description is not encodable in ISO 8859-1')
            raise ValueError('description')
        if not value.isprintable():
            error(f"Proposed description has non-printable characters")
            raise ValueError('description')

        # Make the change in the API, which triggers a refresh.
        self._update('description', value)

    @filter.setter  # type: ignore[no-redef,attr-defined]
    def filter(
        self,
        value: str | WorkgroupFilter,
    ) -> None:
        """Set the new filter.

        See :py:property:`filter` for information on this property.
        You must be a workgroup administrator to use this property setter.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        if isinstance(value, WorkgroupFilter):
            value_as_enum = value
        else:
            value_as_enum = WorkgroupFilter.from_str(value)
        value_as_str = str(value_as_enum)
        # Make the change in the API, which triggers a refresh.
        self._update('filter', value_as_str)

    @privgroup.setter  # type: ignore[no-redef,attr-defined]
    def privgroup(
        self,
        value: bool
    ) -> None:
        """Set the new privgroup value.

        See :py:property:`privgroup` for information on this property.
        You must be a workgroup administrator to use this property setter.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        if not isinstance(value, bool):
            raise TypeError(value)
        if value == True:
            value_as_str = 'TRUE'
        else:
            value_as_str = 'FALSE'
        # Make the change in the API, which triggers a refresh.
        self._update('privgroup', value_as_str)

    @reusable.setter  # type: ignore[no-redef,attr-defined]
    def reusable(
        self,
        value: bool,
    ) -> None:
        """Set the new reusable value.

        See :py:property:`reusable` for information on this property.
        You must be a workgroup administrator to use this property setter.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        if not isinstance(value, bool):
            raise TypeError(value)
        if value == True:
            value_as_str = 'TRUE'
        else:
            value_as_str = 'FALSE'
        # Make the change in the API, which triggers a refresh.
        self._update('reusable', value_as_str)

    @visibility.setter  # type: ignore[no-redef,attr-defined]
    def visibility(
        self,
        value: WorkgroupVisibility | str,
    ) -> None:
        """Set the new visibility.

        See :py:property:`visibility` for information on this property.
        You must be a workgroup administrator to use this property setter.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has been deleted')
        if isinstance(value, WorkgroupVisibility):
            value_as_enum = value
        else:
            value_as_enum = WorkgroupVisibility.from_str(value)
        value_as_str = str(value_as_enum)
        # Make the change in the API, which triggers a refresh.
        self._update('visibility', value_as_str)

    #
    # "D" Methods.
    #

    def delete(self) -> None:
        """Delete the workgroup.

        You must be an administrator in order to delete it.

        .. warning::
            Once a workgroup has been deleted, you may not create a new
            workgroup with the same name.  Stem owners may restore deleted
            workgroups through the Workgroup Manager web site.

        .. note::
            It is possible that the workgroup was already deleted by someone
            else.  If that happens, we will update the instance accordingly,
            and then raise a :class:`WorkgroupDeleted` exception.  If you don't
            care about this case, catch the exception and then continue as
            normal.

        :raises ChildProcessError: Something went wrong on the server side (a
            400 or 500 error was returned).

        :raises PermissionError: You did not use a valid certificate, or do not
            have permissions to perform the operation.

        :raises WorkgroupDeleted: The workgroup has been deleted unexpectedly.

        :raises NotImplementedError: Received an unexpected HTTP response code.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        if self.deleted:
            raise EOFError('Workgroup has (already) been deleted')

        # Make the request to delete the Workgroup.
        response = self.client.client.session.delete(
            self.client._url(
                fragment=self.name
            ),
        )

        # A success is easy to handle, so we can put everything into one big
        # match.
        match response.status_code:
            case 200: # The deletion worked
                debug('Got a response!')
                self._mark_deleted()
            case 400:
                response_json = None
                try:
                    response_json = response.json()
                except requests.exceptions.JSONDecodeError:
                    pass

                # Did our workgroup go inactive out from under us?
                if (
                    response_json is not None and
                    response_json['notification'] == 'Workgroup is inactive'
                ):
                    error(f"Already-instanced workgroup {self.name} has been deleted")
                    self._mark_deleted()
                    raise WorkgroupDeleted(self.name)
                else:
                    # We have a generic 400 error
                    raise ChildProcessError(response.text)
            case 500:
                error(f"Upstream API error: {response.text}")
                raise ChildProcessError(response.text)
            case 401 | 403:
                warning(f"Permission error on get {self.name}")
                raise PermissionError(response.text)
            case 404:
                warning(f"Workgroup {self.name} not found")
                raise KeyError(self.name)
            case _:
                raise NotImplementedError(response.text)

        # All done!
        return None

    #
    # Support Methods
    #

    @staticmethod
    def datestr_to_date(
        datestr: str
    ) -> datetime.date:
        """Convert a Workgroups API date-string to a DateTime Date

        :param datestr: A string in the form "01-Jan-2020"

        :returns: A DateTime Date.

        :raises ValueError: The provided string could not be parsed
        """
        debug(f"Splitting date-string(?) \"{datestr}\"")

        # Split the string into pieces
        pieces = datestr.split('-')
        if len(pieces) != 3:
            raise ValueError('String did not have three components')

        # Try converting the day and year.
        # int() raises a ValueError on problems, so pass that to the caller!
        day_number = int(pieces[0])
        year_number = int(pieces[2])

        # Convert the month into a number
        month_to_number = {
            'JAN': 1,
            'FEB': 2,
            'MAR': 3,
            'APR': 4,
            'MAY': 5,
            'JUN': 6,
            'JUL': 7,
            'AUG': 8,
            'SEP': 9,
            'OCT': 10,
            'NOV': 11,
            'DEC': 12,
        }
        month_str_upper = pieces[1].upper()
        if month_str_upper not in month_to_number:
            raise ValueError(f"Did not recognize month ''{pieces[1]}")
        month_number = month_to_number[month_str_upper]

        # All done!
        result = datetime.date(
            year=year_number,
            month=month_number,
            day=day_number,
        )
        debug(f"Converted date-string to {result}")
        return result
