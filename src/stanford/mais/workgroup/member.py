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

# First, do stdlib imports
import abc
from collections.abc import Iterator, Mapping, MutableSet
import datetime
import enum
import logging
import pathlib
from typing import Any, Literal, TYPE_CHECKING
import weakref

# Finally, do local imports
import stanford.mais.account

# There are some needed type annotations where, if we imported them now, we
# would make an import loop.  So, only import them when type-checking.
if TYPE_CHECKING:
    from stanford.mais.workgroup import PartialWorkgroup
    from stanford.mais.workgroup.workgroup import Workgroup

# Set up logging

logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info
warning = logger.warning
error = logger.error

__all__ = (
    'WorkgroupMembership',
    'WorkgroupMembershipContainer',
    'WorkgroupMembershipPersonContainer',
    'WorkgroupMembershipWorkgroupContainer',
    'WorkgroupMembershipCertificateContainer',
)

# In the same vein as nero_wgcreator.workgroup.enum, this module exists only to
# hold workgroup-related membership stuff.  I did it to keep the size of the
# main module down.  You should expect that everything which appears here will
# be included into the main module.

class WorkgroupMembership:
    """Holds the sets of workgroup members or administrators.

    Each :class:`~stanford.mais.workgroup.Workgroup` includes two instances of
    this class, accessible through the following properties:

    * :meth:`~stanford.mais.workgroup.Workgroup.members` provides access to the
      sets of workgroup members.  As a reminder, this the *real* list of
      workgroup members, without filtering.  See
      :class:`~stanford.mais.workgroup.properties.WorkgroupFilter` for details.

    * :meth:`~stanford.mais.workgroup.Workgroup.administrators` provides access
      to the sets of workgroup administrators.

    Within this class, the members (or administrators) are divided into three
    categories, each of which has its own property accessor:

    * :meth:`people` provides access to the set of members who are people.  The
      values stored are SUNetIDs, and the type is
      :class:`WorkgroupMembershipPersonContainer`.

    * :meth:`workgroups` provides access to the set of nested workgroups.  The
      values stored are fully-qualified workgroup names (in the typical
      'stem:name' form), and the type is
      :class:`WorkgroupMembershipWorkgroupContainer`.

    * :meth:`certificates` provides access to the set of certificates.  The
      values stored are certificate subject common names (CNs), and the type is
      :class:`WorkgroupMembershipCertificateContainer`.

    .. warning::
        If the workgroup's visibility is set to ``PRIVATE``, and you are not an
        administrator of the workgroup, then all workgroup member and
        administrator sets will appear empty.

    Finally, this class supports using :func:`len` to find out the total number
    of workgroup members (or administrators).
    """

    @property
    def people(self) -> WorkgroupMembershipPersonContainer:
        """Access the list of workgroup members that are people.
        """
        return self._people

    @property
    def workgroups(self) -> WorkgroupMembershipWorkgroupContainer:
        """Access the list of nested workgroups.
        """
        return self._workgroups

    @property
    def certificates(self) -> WorkgroupMembershipCertificateContainer:
        """Access the list of workgroup members that are certificates.
        """
        return self._certificates

    def __init__(
        self,
        workgroup: Workgroup,
        collection_type: Literal['members', 'administrators'],
    ) -> None:
        """Return an empty workgroup-membership instance.

        This is used when a container is first instantiated.  Initially, all
        containers start out empty.

        :param workgroup: The containing workgroup.

        :param collection_type: Either `members` or `administrators`.
        """
        debug(f"In init for Workgroup {workgroup.name} WorkgroupMembership {collection_type}")

        # Make empty containers for each type of member or administrator
        self._people=WorkgroupMembershipPersonContainer(
            workgroup=workgroup,
            collection_type=collection_type,
        )
        self._workgroups=WorkgroupMembershipWorkgroupContainer(
            workgroup=workgroup,
            collection_type=collection_type,
        )
        self._certificates=WorkgroupMembershipCertificateContainer(
            workgroup=workgroup,
            collection_type=collection_type
        )

        # All done!
        return None

    def update_from_upstream(
        self,
        response_json: list[Mapping[str, Any]],
    ) -> None:
        """Report new membership details from upstream.

        This is used to update an instance with a new list of members or
        administrators, as received from the Workgroups API.  This is the only
        way to update the instance that does not trigger calls to upstream.

        :param response_json:
            Either the `members` or `administrators` part of the JSON returned
            by the Workgroup API.

        :raises EOFError: The related Workgroup instance no longer exists.
        """
        # For logging, grab the workgroup name & collection type from people
        # Fail if the upstream workgroup no longer exists
        workgroup = self.people.workgroup
        if workgroup is None:
            error('Attempting to update members/administrators for a deleted instance')
            raise EOFError('workgroup')
        collection_type = self.people.collection_type
        debug(f"In update_from_upstream for Workgroup {workgroup.name} type {collection_type}")

        # We get people, certificates, and workgroups all in one list.
        # So, we need to split the list into different sets.
        people = set()
        certificates = set()
        workgroups = set()

        # Add each member to the appropriate set.
        for member in response_json:
            if member['type'] == 'PERSON':
                people.add(member['id'])
            elif member['type'] == 'WORKGROUP':
                workgroups.add(member['id'])
            elif member['type'] == 'CERTIFICATE':
                certificates.add(member['id'])
            else:
                error(f"Found a member of unknown type {member['type']}")
                raise NotImplementedError(member['type'])
        debug(f"Found {len(people)} people, {len(workgroups)} workgroups, {len(certificates)} certs")

        # Pass the sets on to the appropriate containers
        self._people.update_from_upstream(people)
        self._workgroups.update_from_upstream(workgroups)
        self._certificates.update_from_upstream(certificates)

        # All done
        return None

    def __len__(
        self,
    ) -> int:
        """The combined number of people, workgroups, and certificates in this
        set.
        """
        return len(self.people) + len(self.workgroups) + len(self.certificates)

    def __repr__(
        self,
    ) -> str:
        pieces: list[str] = list()

        if len(self.people) > 0:
            pieces.append(f"people={self.people}")
        if len(self.workgroups) > 0:
            pieces.append(f"workgroups={self.workgroups}")
        if len(self.certificates) > 0:
            pieces.append(f"certificates={self.certificates}")

        return 'WorkgroupMembership(' + ','.join(pieces) + ')'


class WorkgroupMembershipContainer(
    MutableSet
):
    """A container for workgroup members: People, Certificates, or Workgroups.
    Instances of this class are used to hold one type of workgroup member.
    Either all people, all certificates, or all workgroups.

    This container acts like a :class:`set`, and so all of the normal set
    methods (like :func:`len` and :func:`~set.add`) are supported.  `in` is
    supported to check for membership.

    .. warning::
        Changes made here result in API calls, changing the Workgroup
        membership.  Be very careful before you do things like calling
        :meth:`~set.clear`.

    .. note::
        Changes made here happen synchronously within the Workgroups API,
        but asynchronously elsewhere.  In other words, when calls like
        :meth:`~set.add` return successfully, you know that the change has been
        made and takes effect immediately within Workgroup Manager, but it will
        take time for the change to propagate to the privgroup, and to
        downstream clients like LDAP.
    """

    _identifiers: set[str]
    """The set of identifiers within this container.
    """

    _workgroup_ref: weakref.ReferenceType[Workgroup]
    """A reference to the containing workgroup.
    """

    _collection_type: Literal['members', 'administrators']
    """The type of collection we have.

    This is either "members" or "administrators".
    """

    # Start with our constructor, then our required methods

    def __init__(
        self,
        workgroup: 'Workgroup',
        collection_type: Literal['members', 'administrators'],
    ) -> None:
        """Return an empty workgroup-membership container instance.

        This is used when a container is first instantiated.  Initially, all
        containers start out empty.

        :param workgroup: The containing workgroup.

        :param collection_type: Either `members` or `administrators`.
        """

        # Save a weakref to the workgroup
        self._workgroup_ref = weakref.ref(workgroup)

        # Save the collection type, and make an empty set of identifiers.
        self._collection_type = collection_type
        self._identifiers = set()

        # All done!
        return None
    
    def update_from_upstream(
        self,
        new_set: set[str],
    ) -> None:
        """Report new membership details from upstream.

        This is used to update an instance with a new list of members or
        administrators, as received from the Workgroups API.  This is the only
        way to update the instance that does not trigger calls to upstream.

        :param new_set:
            The new set of identifiers to store.
        """
        # Try to dereference the workgroup
        workgroup = self._workgroup_ref()
        if workgroup is None:
            workgroup_name = '(Expired instance)'
        else:
            workgroup_name = workgroup.name
        debug(f"In update_from_upstream for Workgroup {workgroup_name} container of {self.collection_type} {self.container_type}")

        # Rather than keeping a reference to the new set, instead we clear our
        # own set, and then update it with the members of the new set.
        self._identifiers.clear()
        self._identifiers.update(new_set)

    @property
    def collection_type(self) -> Literal['members', 'administrators']:
        """The type of collection we are a part of.

        :returns: Either `members` or `administrators`.
        """
        return self._collection_type

    @property
    def workgroup(self) -> Workgroup | None:
        return self._workgroup_ref()

    def __contains__(
        self,
        value: Any,
    ) -> bool:
        """Check if an identifier is in the container.

        :param value: The identifier to check.

        :return: `True` is the identifier is in the container, else `False`.
        """
        return (True if value in self._identifiers else False)

    def __iter__(self) -> Iterator[str]:
        """Return an iterator over the container.
        """
        return iter(self._identifiers)

    def __len__(self) -> int:
        """Return the number of items in the container.
        """
        return len(self._identifiers)

    def add(
        self,
        value: str,
    ) -> None:
        """Add a new identifier to the container.

        This triggers an API call to add the identifier to the workgroup.

        :raises ChildProcessError:
            Something went wrong on the server side (a 400 or 500 error was
            returned).

        :raises EOFError: The related Workgroup instance no longer exists.

        :raises KeyErrror: The identifier was already added.

        :raises PermissionError:
            You did not use a valid certificate, or do not have permissions to
            perform the operation.

        :raises ValueError:
            Workgroup Manager does not know about that identifier.  For
            example, you tried adding a SUNetID that does not exist.

        :raises requests.Timeout:
            The MaIS Workgroup API did not respond in time.
        """
        debug(f"Workgroup TBD: Adding {self.container_type} {value} to {self._collection_type}")

        # Quickly check if we're adding something already added.
        if value in self:
            raise KeyError(value)

        # Resolve the workgroup for later calls
        workgroup = self._workgroup_ref()
        if workgroup is None:
            raise EOFError('workgroup')
        debug(f"Workgroup {workgroup.name}: Adding {self.container_type} {value} to {self._collection_type}")

        # The URL relative path has two parts: The workgroup name and the
        # identifier we're adding.
        url_path = (
            pathlib.PurePosixPath(workgroup.name) /
            pathlib.PurePosixPath(self.collection_type) /
            pathlib.PurePosixPath(value)
        )

        # Get the Requests session
        session = workgroup.client.client.session

        # Do a PUT call to make the add.
        # In addition to the path, we need to provide the identifier type.
        response = session.put(
            workgroup._client._url(
                fragment=url_path,
            ),
            json={'type': self.container_type},
        )

        # Catch a number of bad errors.
        if response.status_code in (400, 500):
            raise ChildProcessError(response.text)
        if response.status_code in (401, 403):
            raise PermissionError('add')
        if response.status_code == 404:
            raise ValueError(response.text)

        # Reset the workgroup's last_updated date
        workgroup._reset_last_update()

        # Add the item to the local set, and that's it!
        self._identifiers.add(value)
        return None

    def discard(
        self,
        value: str,
    ) -> None:
        """Remove an identifier from the container.

        This triggers an API call to remove the identifier from the workgroup.

        :raises ChildProcessError: Something went wrong on the server side (a 400 or 500 error was returned).

        :raises EOFError: The related Workgroup instance no longer exists.

        :raises KeyError: The identifier was already removed.

        :raises PermissionError: You did not use a valid certificate, or do not have permissions to perform the operation.

        :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
        """
        debug(f"Workgroup TBD: Discarding {self.container_type} {value} from {self._collection_type}")

        # Quickly check if we're removing a member already not present.
        if value not in self:
            raise KeyError(value)

        # Resolve the workgroup for later calls
        workgroup = self.workgroup
        if workgroup is None:
            raise EOFError('workgroup')
        debug(f"Workgroup {workgroup.name}: Discarding {self.container_type} {value} from {self._collection_type}")

        # The URL relative path has two parts: The workgroup name and the
        # identifier we're removing.
        url_path = (
            pathlib.PurePosixPath(workgroup.name) /
            pathlib.PurePosixPath(self.collection_type) /
            pathlib.PurePosixPath(value)
        )

        # Get the Requests session
        session = workgroup.client.client.session

        # Do a DELETE call to do the removal.
        # In addition to the path, we need to provide the identifier type.
        response = session.delete(
            workgroup._client._url(
                fragment=url_path,
            ),
            json={'type': self.container_type},
        )

        # Catch a number of bad errors.
        if response.status_code in (400, 500):
            raise ChildProcessError(response.text)
        if response.status_code in (401, 403):
            raise PermissionError('discard')
        if response.status_code == 404: # Just in case
            raise KeyError(response.text)

        # Reset the workgroup's last_updated date
        workgroup._reset_last_update()

        # Remove from the local set, and that's it!
        self._identifiers.discard(value)
        return None

    # Now some helpful underscore methods

    def __str__(self) -> str:
        return str(self._identifiers)

    # A helpful alias, to support `del ...['sunetid']` and the like.
    def __delitem__(
        self,
        value: str
    ) -> None:
        return self.remove(value)

    # Finally, some abstract methods

    @property
    @abc.abstractmethod
    def container_type(self) -> str:
        """The type of identifiers stored in this container.
        """
        ...


class WorkgroupMembershipPersonContainer(WorkgroupMembershipContainer):
    """A read-write container of people.

    .. note::
        If your client certificate is not a workgroup administrator, then the
        container will be read-only.

    This is a set of strings, where each string is a SUNetID.  Attempting to
    add something which is not a SUNetID will raise a `ValueError`.

    .. note::
        At this time, instead of a `ValueError`, a `ChildProcessError` will be
        raised.  TODO: Report this issue to MaIS.

    .. warning::
        The Workgroups API only supports SUNetIDs.  It does not support SUNet
        aliases.  For example, `akkornel` is a SUNetID (acceptable), and
        `karl.kornel` is a SUNet alias (not acceptable).
    """

    @property
    def container_type(self) -> str:
        return 'USER'


class WorkgroupMembershipWorkgroupContainer(WorkgroupMembershipContainer):
    """A read-write container of workgroups.

    .. note::
        If your client certificate is not a workgroup administrator, then the
        container will be read-only.

    This is a set of strings, where each string is a workgroup name in full
    `stem:name` form.  For example, ``research-computing:sysadmins`` is a
    fully-qualified workgroup name.

    For convenience, the following methods accept a :class:`~stanford.mais.workgroup.Workgroup`
    or :class:`~stanford.mais.workgroup.PartialWorkgroup` instance, in addition
    to a string:

    * :meth:`~frozenset.add`

    * :meth:`~frozenset.discard`

    * :meth:`~object.__contains__` (also known as ``in``)

    .. note::
        Regardless of what you :meth:`~set.add` — :class:`str`,
        :class:`~stanford.mais.workgroup.Workgroup` or
        :class:`~stanford.mais.workgroup.PartialWorkgroup` — the set will only
        ever contain (and return) strings.

    Attempting to add something which is not a workgroup will raise a
    `ValueError`.
    """

    @property
    def container_type(self) -> str:
        return 'WORKGROUP'

    def add(
        self,
        value: str | PartialWorkgroup | Workgroup,
    ) -> None:
        """Add a workgroup to the set.

        This is also called "nesting a workgroup".

        :param value: The fully-qualified workgroup name, or an instance of
            :class:`~stanford.mais.workgroup.PartialWorkgroup` or
            :class:`~stanford.mais.workgroup.Workgroup`.
        """
        if isinstance(value, str):
            # If we were given a string, send it through.
            super().add(value)
        else:
            # If we were given a workgroup instance, or a partial workgroup
            # from a search result, grab the name and send *that* through.
            super().add(value.name)

    def discard(
        self,
        value: str | PartialWorkgroup | Workgroup,
    ) -> None:
        """Remove a workgroup from the set.

        :param value: The fully-qualified workgroup name, or an instance of
            :class:`~stanford.mais.workgroup.PartialWorkgroup` or
            :class:`~stanford.mais.workgroup.Workgroup`.
        """
        if isinstance(value, str):
            # If we were given a string, send it through.
            super().discard(value)
        else:
            # If we were given a workgroup instance, or a partial workgroup
            # from a search result, grab the name and send *that* through.
            super().discard(value.name)

    def __contains__(
        self,
        value: Any,
    ) -> bool:
        """Check if a workgroup is in the set.

        :param value: The fully-qualified workgroup name, or an instance of
            :class:`~stanford.mais.workgroup.PartialWorkgroup` or
            :class:`~stanford.mais.workgroup.Workgroup`.

        :returns: ``True`` if the workgroup is in the set, else ``False``.
        """
        if isinstance(value, str):
            # If we were given a string, send it through.
            return super().__contains__(value)
        else:
            # If we were given a workgroup instance, or a partial workgroup
            # from a search result, grab the name and send *that* through.
            return super().__contains__(value.name)


class WorkgroupMembershipCertificateContainer(WorkgroupMembershipContainer):
    """A read-write container of certificates.

    .. note::
        If your client certificate is not a workgroup administrator, then the
        container will be read-only.

    Certificates are identified by their "common name".  This is the `CN` part
    of the certificate's Subject.

    Attempting to add something which is not a certificate will raise a
    `ValueError`.

    .. note::
        In almost all cases, certificates may only be workgroup administrators.
        Attempting to add a certificate as a workgroup member will raise a
        `ChildProcessError`.
    """

    @property
    def container_type(self) -> str:
        return 'CERTIFICATE'
