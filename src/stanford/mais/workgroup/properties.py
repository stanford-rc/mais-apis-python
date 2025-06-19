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

import enum
import logging
from typing import *

# Set up logging

logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info

__all__ = (
    'WorkgroupVisibility',
    'WorkgroupFilter',
)

# This module exists only to hold the workgroup-related Enums.  I did it to
# keep the size of the main module down.  You should expect that everything
# which appears here will be included into the main module.

WorkgroupFilterLiteral = Literal[
    'NONE',
    'ACADEMIC_ADMINISTRATIVE',
    'STUDENT',
    'FACULTY',
    'STAFF',
    'FACULTY_STAFF',
    'FACULTY_STUDENT',
    'STAFF_STUDENT',
    'FACULTY_STAFF_STUDENT',
]

@enum.unique
class WorkgroupFilter(enum.Enum):
    """Options for filtering Workgroup membership.

    By default, any active SUNetID may be a workgroup member or administrator.  
    With filters, it is possible to change that.

    If you set a filter on a workgroup, the *effective* membership (which
    downstream consumers will see) is determined using the following process:

    1. Flatten the workgroup.  For every workgroup that has been nested into
       this workgroup, run this flattening/filtering process on that workgroup,
       and then add the resulting membership to this workgroup.

    2. Using the now-flatted list, evaluate each member against the selected
       filter.  If the workgroup member does not match the selected filter,
       remove them.

    3. The resulting list is the *effective* workgroup membership that others
       see.

    The resulting list is used by downstream workgroups (that this workgroup is
    nested in), and is also used when you fetch the privgroup for the
    workgroup.

    If you use this API to add someone who does not match the filter, the
    action will complete successfully.  Whenever a person changes status, all
    related workgroups have their memberships re-computed automatically.  For
    example, if you add a non-student to a staff-only workgroup, and they
    become staff the next day, they will suddenly become "in" the workgroup.

    .. note::
        When you use :attr:`~stanford.mais.workgroup.Workgroup.members` and
        :attr:`~stanford.mais.workgroup.Workgroup.administrators`, you are
        accessing the *real* lists.  To see the *effective* lists, use
        :meth:`~stanford.mais.workgroup.Workgroup.get_privgroup`.

    .. note::
        Once a SUNetID goes inactive (for example, by a student having
        graduated), the SUNetID is **removed** from the workgroup—both the real
        and effective lists—shortly after the SUNetID goes inactive.  This
        cleanup mechanism is not affected by filters.  If you have questions,
        or do not want it to apply to your workgroup stem, contact MaIS.

    .. note::
        Normally, calling :func:`str` on an :class:`~enum.Enum` will result in
        a fully-qualified string (for example, ``WorkgroupFilter.NONE``).
        If you cal' :func:`str` here, only the value (for example, ``NONE``)
        will be returned.
    """

    NONE = 0
    """No membership filters are set."""

    ACADEMIC_ADMINISTRATIVE = 1
    """Limit effective membership to faculty, staff, students, and sponsored
    SUNetIDs.
    """

    STUDENT = 2
    """Limit effective membership to students."""

    FACULTY = 3
    """Limit effective membership to faculty."""

    STAFF = 4
    """Limit effective membership to staff."""

    FACULTY_STAFF = 5
    """Limit effective membership to faculty & staff."""

    FACULTY_STUDENT = 6
    """Limit effective membership to faculty & students."""

    STAFF_STUDENT = 7
    """Limit effective membership to staff & students."""

    FACULTY_STAFF_STUDENT = 8
    """Limit effective membership to faculty, staff, and students.

    This is similar to, but more restrictive than, ``ACADEMIC_ADMINISTRATIVE``.
    """

    def __str__(self) -> str:
        """Convert an enum to a string.

        See the class documentation for notes.

        :return: The name of the enum value, in string form.
        """
        return self.name

    @staticmethod
    def from_str(value: str) -> 'WorkgroupFilter':
        """Convert a string into an enum.

        :param visibility: The string to convert.  Is case-sensitive.

        :raises ValueError: The value provided does not match an enum value.
        """
        if value == 'NONE':
            return WorkgroupFilter.NONE
        elif value == 'ACADEMIC_ADMINISTRATIVE':
            return WorkgroupFilter.ACADEMIC_ADMINISTRATIVE
        elif value == 'STUDENT':
            return WorkgroupFilter.STUDENT
        elif value == 'FACULTY':
            return WorkgroupFilter.FACULTY
        elif value == 'STAFF':
            return WorkgroupFilter.STAFF
        elif value == 'FACULTY_STAFF':
            return WorkgroupFilter.FACULTY_STAFF
        elif value == 'FACULTY_STUDENT':
            return WorkgroupFilter.FACULTY_STUDENT
        elif value == 'STAFF_STUDENT':
            return WorkgroupFilter.STAFF_STUDENT
        elif value == 'FACULTY_STAFF_STUDENT':
            return WorkgroupFilter.FACULTY_STAFF_STUDENT
        else:
            raise ValueError(value)

@enum.unique
class WorkgroupVisibility(enum.Enum):
    """Options for workgroup membership visibility.

    Workgroup administrators may control the visibility of workgroup's
    membership.  The different options available are defined here.

    .. note::
        Normally, calling :func:`str` on an :class:`~enum.Enum` will result in
        a fully-qualified string (for example, ``WorkgroupVisibility.PRIVATE``).
        If you call :func:`str` here, only the value (for example, ``PRIVATE``)
        will be returned.
    """

    STANFORD = 0
    """The workgroup's lists of members and administrators are visibile to all
    authenticated users.
    """

    PRIVATE = 1
    """The workgroup's lists of members and administrators are only visibile to
    workgroup administrators.  To everyone else, the workgroup will appear
    empty.

    .. danger::
        This limitation applies within Workgroup Manager and the Workgroup API,
        and it applies to **some** downstream applications, but not all!

        For example, LDAP receives member and administrator information for all
        workgroups, including private workgroups.  However, Stanford Login does
        not.  So, private workgroups may not be used for authentication.
    """

    def __str__(self) -> str:
        """Convert an enum to a string.

        See the class documentation for notes.

        :return: The name of the enum value, in string form.
        """
        return self.name

    @staticmethod
    def from_str(visibility: str) -> 'WorkgroupVisibility':
        """Convert a string into an enum.

        :param visibility: The string to convert.  It is case-sensitive.

        :raises ValueError: The value provided does not match an enum value.
        """
        if visibility == 'PRIVATE':
            return WorkgroupVisibility.PRIVATE
        elif visibility == 'STANFORD':
            return WorkgroupVisibility.STANFORD
        else:
            raise ValueError(visibility)
