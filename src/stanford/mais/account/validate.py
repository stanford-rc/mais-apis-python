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

import functools
import logging
import re
from typing import *
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

class AccountValidationResults(NamedTuple):
    """Results of doing an account validation.

    This class contains the results of an account validation, called via
    :func:`validate`.
    """

    raw: Optional[str]
    """
    The raw input provided for validation.  This is only provided when
    a string was provided to :func:`validate`.
    """

    raw_set: Collection[str]
    """
    The raw input provided for validation.  If a string was provided to
    :func:`validate`, then this is the raw input after being split into a
    collection.  Otherwise, this will be the original list/set/tuple that was
    provided to :func:`validate`, but made into a set.

    The set union of `full`, `base`, `inactive`, and `unknown` should equal
    this list.
    """

    full: Collection[str]
    """
    The list of active, full (or full-sponsored) SUNetIDs found in `raw_set`.
    """

    base: Collection[str]
    """
    The list of active, base (or base-sponsored) SUNetIDs found in `raw_set`.
    """

    inactive: Collection[str]
    """
    The list of inactive SUNetIDs found in `raw_set`.
    """

    unknown: Collection[str]
    """
    The list of entries from `raw_set` that are not SUNetIDs.
    """

@functools.singledispatch
def validate(
    raw: str,
    client: stanford.mais.account.AccountClient,
) -> AccountValidationResults:
    """Given a list of SUNetIDs, in string or collection form, validate and
    check status.

    This takes a list of SUNetIDs, and returns a list of SUNetIDs which have
    been checked against the Accounts API for both activity and service level.
    The returned result shows which SUNetIDs are active full (or
    full-sponsored), active base (or base-sponsored), or inactive.

    If the input is a string, then the input string may be separated by commas,
    and/or any kind of whitespace.  If the input is some other form of
    collection (list, tuple, or set), the function assumes that all whitespace
    etc. have been removed.

    This is designed to catch most exceptions.  Exceptions related to
    validation (for example, attempting to validate an obviously-invalid
    SUNetID like `ab$#`) will result in the 'SUNetID' being added to the
    `unknown` list, instead of throwing an exception.  The only exceptions that
    should be expected from this function are ones related to API issues.

    :param raw: The list of SUNetIDs.  If a `str`, then the list may be comma- and/or whitespace-separated.

    :param client: An :class:`~stanford.mais.account.AccountClient` to connect to the Account API.

    :return: The results of the validation.  See the definition of :class:`~nero_wgcreator.account.validate.AccountValidationResults` for details.  If the input to this function is a string; that string will be in `raw`, and the parsed list will be in `raw_set`.  If the input to this function is not a string, then `raw` will be `None` and `raw_set` will be a copy of the input.

    :raises ChildProcessError: Something went wrong on the server side (a 400 or 500 error was returned).

    :raises PermissionError: You did not use a valid certificate, or do not have permissions to perform the operation.

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
    result = validate(raw_list_filtered, client)

    # Add in our raw string, and we're done!
    return AccountValidationResults(
        raw=raw,
        raw_set=result.raw_set,
        full=result.full,
        base=result.base,
        inactive=result.inactive,
        unknown=result.unknown,
    )

@validate.register(list)
@validate.register(tuple)
@validate.register(set)
def _(
    raw: Union[List[str], Tuple[str], Set[str]],
    client: stanford.mais.account.AccountClient,
) -> AccountValidationResults:
    """
    (This is a single-dispatch function.  See the documentation above!
    """
    debug('In validate with list/tuple/set')
    debug('Input: ' + ','.join(raw))
    debug(f"Input has {len(raw)} items.")

    # Limit our accounts to only people
    people = client.only_people()

    # If we were not given a set, then convert it into a set.
    if not isinstance(raw, set):
        raw = set(raw)

    # Components of the output
    full = set()
    base = set()
    inactive = set()
    unknown = set()

    for sunetid in raw:
        # Catch unknown entries
        try:
            account = people.get(sunetid)
            debug(f"Account {sunetid} exists.")
        except (ValueError, IndexError, KeyError):
            debug(f"Account {sunetid} not found.")
            unknown.add(sunetid)
            continue

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
        raw_set=raw,
        full=full,
        base=base,
        inactive=inactive,
        unknown=unknown,
    )
