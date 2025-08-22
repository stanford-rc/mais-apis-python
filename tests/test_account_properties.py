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

import datetime
import itertools
import pytest
from stanford.mais.client import MAISClient
from stanford.mais.account import AccountClient, Account
from stanford.mais.account.service import ServiceStatus


"""
This tests all of the properties that can be returned within an Account.

All test accounts (that aren't intentionally broken) have:
    - sunetid
    - name
    - description
    - last_update

These are our test users:
    fullprsn:
        is_person is True
        is_active is True
        is_full is True
        has:
            kerberos
            library
            seas
            email
            leland
            pts
            afs
            dialin
    frozprsn:
        Like fullprsn, but Kerberos is frozen
        Also has SUNetID aliases
        Also has autoreply enabled
    formerpsn:
        is_person is True
        is_active is False
        is_full is False
        has:
            (nothing)
    affilite:
        is_person is True
        is_active is True
        is_full is True
        has:
            kerberos
            seas
            email
            leland
            pts
            afs
            dialin
    afilbase:
        is_person is True
        is_active is True
        is_full is False
        has:
            kerberos
    functional:
        is_person is False
        is_active is True
        is_full is False
        has:
            kerberos
            pts
            afs
    oldfunctional:
        is_person is False
        is_active is False
        is_full is False
        has:
            (nothing)
    sharedmailbox:
        is_person is False
        is_active is True
        is_full is False
        has:
            seas
            email
            autoreply
"""

# Test that we get the expected SUNetIDs
def test_sunetid(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # Check that SUNetIDs match what we expect
    assert fullprsn.sunetid == 'fullprsn'
    assert frozprsn.sunetid == 'frozprsn'
    assert formerpsn.sunetid == 'formerpsn'
    assert affilite.sunetid == 'affilite'
    assert afilbase.sunetid == 'afilbase'
    assert functional.sunetid == 'functional'
    assert oldfunctional.sunetid == 'oldfunctional'
    assert sharedmailbox.sunetid == 'sharedmailbox'

# Test that we get the expected names
def test_name(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # Check that names match what we expect
    assert fullprsn.name == 'Person, Full'
    assert frozprsn.name == 'Person, Frozen'
    assert formerpsn.name == 'Person, Former'
    assert affilite.name == 'Smith, Affiliate'
    assert afilbase.name == 'Jones, Base Affiliate'
    assert functional.name == 'Functional Account'
    assert oldfunctional.name == 'Old Functional Account'
    assert sharedmailbox.name == 'Some Group Mailbox - shared email'

# Test that we get the expected descriptions
def test_description(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # Check that descriptions match what we expect
    assert fullprsn.description == 'Staff - University IT'
    assert frozprsn.description == 'Staff - University IT'
    assert formerpsn.description == 'Former Staff - University IT'
    assert affilite.description == 'Affiliate - Genetics'
    assert afilbase.description == 'Affiliate - Anesthesia'
    assert functional.description == 'Functional Account'
    assert oldfunctional.description == 'Functional Account'
    assert sharedmailbox.description == 'Shared mailbox for some group'

def test_is_person(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # Check that is_person matches what we expect
    assert fullprsn.is_person is True
    assert frozprsn.is_person is True
    assert formerpsn.is_person is True
    assert affilite.is_person is True
    assert afilbase.is_person is True
    assert functional.is_person is False
    assert oldfunctional.is_person is False
    assert sharedmailbox.is_person is False

def test_is_active(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # Check that is_active matches what we expect
    assert fullprsn.is_active is True
    assert frozprsn.is_active is True
    assert formerpsn.is_active is False
    assert affilite.is_active is True
    assert afilbase.is_active is True
    assert functional.is_active is True
    assert oldfunctional.is_active is False
    assert sharedmailbox.is_active is True

def test_is_full(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # Check that is_full matches what we expect
    assert fullprsn.is_full is True
    assert frozprsn.is_full is True
    assert formerpsn.is_full is False
    assert affilite.is_full is True
    assert afilbase.is_full is False
    assert functional.is_full is False
    assert oldfunctional.is_full is False
    assert sharedmailbox.is_full is False

# Test last_update
def test_last_updated(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # All our test accounts have the same last-updated datetime
    expected_dt = datetime.datetime(
        year=2020,
        month=1,
        day=3,
        hour=15,
        minute=14,
        second=13,
        microsecond=0,
        tzinfo=datetime.timezone.utc,
    )

    # Test last-updated is decoded correctly
    assert fullprsn.last_update == expected_dt
    assert frozprsn.last_update == expected_dt
    assert formerpsn.last_update == expected_dt
    assert affilite.last_update == expected_dt
    assert afilbase.last_update == expected_dt
    assert functional.last_update == expected_dt
    assert oldfunctional.last_update == expected_dt
    assert sharedmailbox.last_update == expected_dt
