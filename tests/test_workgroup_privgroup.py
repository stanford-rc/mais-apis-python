# vim: ts=4 sw=4 et
# -*- coding: utf-8 -*-

# © 2025 The Board of Trustees of the Leland Stanford Junior University.
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
import datetime
import itertools
import pytest
from stanford.mais.client import MAISClient
from stanford.mais.workgroup import WorkgroupClient, Workgroup, WorkgroupDeleted


"""
Test getting the privilege group for a workgroup.
"""


# Test getting & checking the privgroup of test:1
# NOTE: The return type is included here to quiet MyPy complaints.
def test_get_test1(workgroup_client) -> None:
    workgroup = workgroup_client['test:1']
    privgroup = workgroup.get_privgroup()

    # A small dataclass to represent expected privgroup entries
    @dataclasses.dataclass(eq=True, frozen=True)
    class ExpectedEntry:
        lastUpdate: datetime.date
        name: str
        sunetid: str

    # These are our expected results
    expected_members = {
        ExpectedEntry(
            lastUpdate=datetime.date(2025, 1, 1),
            name='Kornel, Karl',
            sunetid='akkornel'
        ),
    }
    expected_administrators = {
        ExpectedEntry(
            lastUpdate=datetime.date(2025, 1, 1),
            name='Stanford, Leland Jr.',
            sunetid='stanford',
        ),
    }

    # Check we got the expected number of results
    assert len(privgroup.members) == len(expected_members)
    assert len(privgroup.administrators) == len(expected_administrators)

    # Check each expected member result
    for member in privgroup.members:
        # For each member, look for a match from our expected set
        match_found = False
        for possible_match in expected_members:
            if possible_match.sunetid == member.sunetid:
                # We found a match!  Make sure the match is right
                assert possible_match.lastUpdate == member.last_update
                assert possible_match.name == member.name
                match_found = True

                # Before exiting the loop, remove from the set
                expected_members.remove(possible_match)
                break

        # Did we find everyone?
        assert match_found is True

    # Did we find all our members?
    assert len(expected_members) == 0

    # Check each expected member result
    for member in privgroup.administrators:
        # For each member, look for a match from our expected set
        match_found = False
        for possible_match in expected_administrators:
            if possible_match.sunetid == member.sunetid:
                # We found a match!  Make sure the match is right
                assert possible_match.lastUpdate == member.last_update
                assert possible_match.name == member.name
                match_found = True

                # Before exiting the loop, remove from the set
                expected_administrators.remove(possible_match)
                break

        # Did we find everyone?
        assert match_found is True

    # Did we find all our members?
    assert len(expected_administrators) == 0

# Getting the privgroup of a workgroup we can't access raises PermissionError
# NOTE: This is meant to test the preëmptive PermissionError that
# get_privgroup() raises when can_see_members() is False.
def test_get_private(workgroup_client):
    workgroup = workgroup_client['private:1']

    with pytest.raises(PermissionError):
        workgroup.get_privgroup()

# Use special workgroup names to test upstream failures, including
# PermissionError coming from the API.
def test_bad(workgroup_client):
    # Each test follows the same pattern:
    # * Fetch test:1
    # * Change name internally
    # * Get privgroup, expecting an exception
    # * Clear cache

    # 400 (inactive workgroup)
    result1 = workgroup_client['test:1']
    result1._name = 'test:inactive'
    with pytest.raises(WorkgroupDeleted):
        result1.get_privgroup()
    workgroup_client.clear_cache()

    # 400 (not inactive workgroup)
    result2 = workgroup_client['test:1']
    result2._name = 'bad:w1'
    with pytest.raises(ChildProcessError):
        result2.get_privgroup()
    workgroup_client.clear_cache()

    # 401
    result3 = workgroup_client['test:1']
    result3._name = 'bad:w3'
    with pytest.raises(PermissionError):
        result3.get_privgroup()
    workgroup_client.clear_cache()

    # 403
    result4 = workgroup_client['test:1']
    result4._name = 'bad:w4'
    with pytest.raises(PermissionError):
        result4.get_privgroup()
    workgroup_client.clear_cache()

    # 500
    result5 = workgroup_client['test:1']
    result5._name = 'bad:w2'
    with pytest.raises(ChildProcessError):
        result5.get_privgroup()
    workgroup_client.clear_cache()

    # 521 (some response code we do not expect)
    result6 = workgroup_client['test:1']
    result6._name = 'bad:w6'
    with pytest.raises(NotImplementedError):
        result6.get_privgroup()
    workgroup_client.clear_cache()
