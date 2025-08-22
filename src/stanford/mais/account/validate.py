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

from collections.abc import Collection
import dataclasses
import functools
import logging
import re
import stanford.mais.account

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info

__all__ = (
    'validate',
    'AccountValidationResults',
)

# In __all__, we list `validate` first.  But in the code, we define the results
# class first.  That is so that we can reference the class name directly in
# `validate`.

@dataclasses.dataclass(frozen=True, slots=True, weakref_slot=True)
class AccountValidationResults:
    """Results of doing an account validation.

    This class contains the result of calling :func:`validate`.
    """

    raw: str | None
    """
    The raw input string provided for validation.  This is only provided when
    a string was provided to :func:`validate`.
    """

    raw_set: Collection[str]
    """
    The raw input provided for validation.  If a string was provided to
    :func:`validate`, then this is the raw input after being split.  If the
    input to :func:`validate` was a set, then this is that set.  Otherwise,
    this is the input to :func:`validate`, but as a set.

    The set union of ``full``, ``base``, ``inactive``, and ``unknown`` is equal
    to this.
    """

    full: Collection[str]
    """
    The set of active full (or full-sponsored) SUNetIDs found in ``raw_set``.
    """

    base: Collection[str]
    """
    The set of active base (or base-sponsored) SUNetIDs found in ``raw_set``.
    """

    inactive: Collection[str]
    """
    The set of inactive SUNetIDs found in ``raw_set``.
    """

    unknown: Collection[str]
    """
    The set of entries from ``raw_set`` that are not SUNetIDs.  This includes
    uids that are functional accounts.
    """

# For validation, we will have three functions:
# * Our first function handles strings, and splitting them up.
#   This is also the named function, so our documentation is here.
# * The second function handles collections of strings.
# * The third function does the actual validation work.
# We have three functions because each function needs to process the validation
# results a little bit, before returning them to the client.
@functools.singledispatch
def validate(
    raw: str,
    client: stanford.mais.account.AccountClient,
) -> AccountValidationResults:
    """Given a list of SUNetIDs—as a :class:`str`, :class:`list`,
    :class:`tuple`, :class:`set`, or :class:`frozenset`—validate
    and check status.

    This takes a list of SUNetIDs, and returns a list of SUNetIDs which have
    been checked against the Accounts API for both activeness and service
    level.  The returned result shows which SUNetIDs are active full (or
    full-sponsored), active base (or base-sponsored), or inactive.  All other
    entries (including those representing functional accounts) are rejected as
    "unknown".

    If the input is a string, then the input string may be separated by commas,
    and/or whitespace, (where "whitespace" is a space, newline/linefeed, form
    feed, carriage return, tab/horizontal tab, or vertical tab character).  If
    the input is a list, tuple, or set; the function assumes that all
    whitespace etc. have been removed.

    .. note::
       "List, tuple, set, or frozenset" is used instead of the generic
       :class:`~collections.abc.Collection` because a :class:`str` is also a
       collection (of one-character :class:`str`).
       See `typing issue #256 <https://github.com/python/typing/issues/256>`_
       for the discussion around this issue.

    This is designed to catch most exceptions.  Exceptions related to
    validation (for example, attempting to validate an obviously-invalid
    SUNetID like ``ab$#``) will result in the 'SUNetID' being added to the
    `unknown` list, instead of throwing an exception.  The only exceptions that
    should be expected from this function are ones related to API issues.

    :param raw: The list of SUNetIDs.  If a :class:`str`, then the list must be
       either comma- and/or whitespace-separated.

    :param client: An :class:`~stanford.mais.account.AccountClient` to connect
       to the Account API.

    :return: The results of the validation.  See
       :class:`AccountValidationResults` for details.

    :raises ChildProcessError: Something went wrong on the server side (a 400
       or 500 error was returned).

    :raises PermissionError: You did not use a valid certificate, or do not
       have permissions to perform the operation.

    :raises requests.Timeout: The MaIS Workgroup API did not respond in time.
    """
    debug('In validate with str')
    debug(f"Validation input: {raw}")

    # Start by spliting on whitespace and comma.
    # NOTE: Repeated instances of whitespace/separators will make empty entries.
    raw_list = re.split(r'\s|,', raw)

    # Filter out all empty entries, and remove duplicates by using the set.
    debug(f"Split list pre-filter has {len(raw_list)} items.")
    raw_list_filtered = set(filter(
        lambda item: len(item)>0,
        raw_list
    ))

    # Validate the list entries.
    debug(f"Post-filter list has {len(raw_list_filtered)} items.")
    result = _validate(raw_list_filtered, client)

    # Add in our raw string, and we're done!
    return AccountValidationResults(
        raw=raw,
        raw_set=result.raw_set,
        full=result.full,
        base=result.base,
        inactive=result.inactive,
        unknown=result.unknown,
    )

# At this time, MyPy has a problem with the type-checking single-dispatch
# functions.  See https://github.com/python/mypy/issues/13040
@validate.register(list)
@validate.register(tuple)
@validate.register(set)
@validate.register(frozenset)
def _( # type: ignore[misc]
    raw: list[str] | tuple[str] | set[str] | frozenset[str],
    client: stanford.mais.account.AccountClient,
) -> AccountValidationResults:
    """
    (This is a single-dispatch function.  See the documentation above!
    """
    debug('In validate with list/tuple/set')
    debug('Input: ' + ','.join(raw))
    debug(f"Input has {len(raw)} items.")

    # If we were not given a set, then convert it into a set.
    if not isinstance(raw, set):
        raw = set(raw)

    # Get the results
    result = _validate(raw, client)

    # Add in our original raw, and we're done!
    return AccountValidationResults(
        raw=None,
        raw_set=raw,
        full=result.full,
        base=result.base,
        inactive=result.inactive,
        unknown=result.unknown,
    )

# Do the actual validation here!
def _validate(
    sunetids: set[str],
    client: stanford.mais.account.AccountClient,
) -> AccountValidationResults:
    # Components of the output
    full = set()
    base = set()
    inactive = set()
    unknown = set()

    # Limit our accounts to only people
    people = client.only_people()

    for sunetid in sunetids:
        # Catch unknown entries
        try:
            account = people.get(sunetid)
            debug(f"Account {sunetid} exists.")
        except (ValueError, IndexError, KeyError):
            debug(f"Account {sunetid} not found.")
            unknown.add(sunetid)
            continue

        # Overwrite the input SUNetID with the normalized one.
        sunetid = account.sunetid

        # Next, catch inactives
        if account.is_active is False:
            debug(f"Account {sunetid} NOT active.")
            inactive.add(sunetid)
            continue

        # Finally, sort into full or base
        if account.is_full:
            debug(f"Account {sunetid} is FULL")
            full.add(sunetid)
        else:
            debug(f"Account {sunetid} is base")
            base.add(sunetid)

    # Return the structure
    debug(f"Validation results: full={len(full)} base={len(base)} inactive={len(inactive)} unknown={len(unknown)}")
    return AccountValidationResults(
        raw=None,
        raw_set=sunetids,
        full=frozenset(full),
        base=frozenset(base),
        inactive=frozenset(inactive),
        unknown=frozenset(unknown),
    )
