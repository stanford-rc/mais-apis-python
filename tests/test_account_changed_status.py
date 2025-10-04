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

import datetime
import itertools
import pytest
from stanford.mais.client import MAISClient
from stanford.mais.account import AccountClient


"""Test "Get Accounts Changed Status in X Days" API
"""

# Check that invalid days values are rejected
def test_account_changed_status_badqueries(account_client):
    with pytest.raises(ValueError):
        account_client.get_changed_status(
            days=-1,
            current_status='active',
            get_people=True,
        )
    with pytest.raises(ValueError):
        account_client.get_changed_status(
            days=0,
            current_status='active',
            get_people=True,
        )
    with pytest.raises(ValueError):
        account_client.get_changed_status(
            days=31,
            current_status='active',
            get_people=True,
        )

# Test handling of 403 and 500 codes
def test_account_changed_status_bad(account_client):
    with pytest.raises(ChildProcessError):
        account_client.get_changed_status(
            days=2,
            current_status='pending',
            get_people=True,
        )
    with pytest.raises(PermissionError):
        account_client.get_changed_status(
            days=2,
            current_status='pending',
            get_people=False,
        )
    with pytest.raises(NotImplementedError):
        account_client.get_changed_status(
            days=3,
            current_status='pending',
            get_people=True,
        )

# Test a search that returns no results
def test_account_changed_status_empty(account_client):
    results = account_client.get_changed_status(
            days=30,
            current_status='pending',
            get_people=True,
        )
    assert len(results) == 0

# Test searches that actually return results 
def test_account_changed_status_person_active(account_client):
    # Do the fetch, and check the # of returned results
    results = account_client.get_changed_status(
            days=30,
            current_status='active',
            get_people=True,
        )
    assert len(results) == 4

    # For each result, check it can load a full account, and that things match
    for result in results:
        full_result = result.account(account_client)

        assert result.sunetid == full_result.sunetid
        assert result.is_person == full_result.is_person
        assert result.is_active == full_result.is_active
        assert result.last_update == full_result.last_update

def test_account_changed_status_person_inactive(account_client):
    # Do the fetch, and check the # of returned results
    results = account_client.get_changed_status(
            days=30,
            current_status='inactive',
            get_people=True,
        )
    assert len(results) == 1

    # For each result, check it can load a full account, and that things match
    for result in results:
        full_result = result.account(account_client)

        assert result.sunetid == full_result.sunetid
        assert result.is_person == full_result.is_person
        assert result.is_active == full_result.is_active
        assert result.last_update == full_result.last_update

def test_account_changed_status_functional_active(account_client):
    # Do the fetch, and check the # of returned results
    results = account_client.get_changed_status(
            days=30,
            current_status='active',
            get_people=False,
        )
    assert len(results) == 2

    # For each result, check it can load a full account, and that things match
    for result in results:
        full_result = result.account(account_client)

        assert result.sunetid == full_result.sunetid
        assert result.is_person == full_result.is_person
        assert result.is_active == full_result.is_active
        assert result.last_update == full_result.last_update

def test_account_changed_status_functional_inactive(account_client):
    # Do the fetch, and check the # of returned results
    results = account_client.get_changed_status(
            days=30,
            current_status='inactive',
            get_people=False,
        )
    assert len(results) == 1

    # For each result, check it can load a full account, and that things match
    for result in results:
        full_result = result.account(account_client)

        assert result.sunetid == full_result.sunetid
        assert result.is_person == full_result.is_person
        assert result.is_active == full_result.is_active
        assert result.last_update == full_result.last_update
