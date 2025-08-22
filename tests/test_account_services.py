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

import itertools
import pytest
from stanford.mais.client import MAISClient
from stanford.mais.account import AccountClient, Account
from stanford.mais.account.service import ServiceStatus

"""
This tests each account to ensure it returns the expected services.

See test_account_properties.py for a list of accounts, and what we expect from
them.
"""

# Test that we can still load an account which has an unknown (to us) service
def test_newservice(account_client):
    # Test we can fetch our account
    newservice = account_client['newservice']

    # It should not have any known service
    assert newservice.services.kerberos is None
    assert newservice.services.seas is None
    assert newservice.services.email is None
    assert newservice.services.leland is None
    assert newservice.services.pts is None
    assert newservice.services.afs is None
    assert newservice.services.library is None
    assert newservice.services.dialin is None
    assert newservice.services.autoreply is None

# Test that accounts of an unknown (to us) type will raise an exception
def test_newtype(account_client):
    with pytest.raises(NotImplementedError):
        newtype = account_client['newtype']

# Test the aspects of the kerberos service
def test_kerberos(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the kerberos service
    assert sharedmailbox.services.kerberos is None

    # These folks should have the kerberos service
    assert fullprsn.services.kerberos is not None
    assert frozprsn.services.kerberos is not None
    assert formerpsn.services.kerberos is not None
    assert affilite.services.kerberos is not None
    assert afilbase.services.kerberos is not None
    assert functional.services.kerberos is not None
    assert oldfunctional.services.kerberos is not None

    # Check active or frozen
    assert fullprsn.services.kerberos.status == ServiceStatus.ACTIVE
    assert frozprsn.services.kerberos.status == ServiceStatus.FROZEN
    assert formerpsn.services.kerberos.status == ServiceStatus.INACTIVE
    assert affilite.services.kerberos.status == ServiceStatus.ACTIVE
    assert afilbase.services.kerberos.status == ServiceStatus.ACTIVE
    assert functional.services.kerberos.status == ServiceStatus.ACTIVE
    assert oldfunctional.services.kerberos.status == ServiceStatus.INACTIVE

    # Check that principal matches SUNetID
    assert fullprsn.services.kerberos.principal == fullprsn.sunetid
    assert frozprsn.services.kerberos.principal == frozprsn.sunetid
    assert formerpsn.services.kerberos.principal == formerpsn.sunetid
    assert affilite.services.kerberos.principal == affilite.sunetid
    assert afilbase.services.kerberos.principal == afilbase.sunetid
    assert functional.services.kerberos.principal == functional.sunetid
    assert oldfunctional.services.kerberos.principal == oldfunctional.sunetid

    # Check that uid is what we expect
    assert fullprsn.services.kerberos.uid == 12345
    assert frozprsn.services.kerberos.uid == 12346
    assert affilite.services.kerberos.uid == 12344
    assert afilbase.services.kerberos.uid == 12333
    assert functional.services.kerberos.uid == 12332

# Test if is_active property works correctly, using the Kerberos service
def test_is_active(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']

    # Check is_active
    assert fullprsn.services.kerberos.is_active is True
    assert frozprsn.services.kerberos.is_active is False
    assert formerpsn.services.kerberos.is_active is False

# Test if not_inactive property works correctly, using the Kerberos service
def test_not_inactive(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']

    # Check not_inactive
    assert fullprsn.services.kerberos.not_inactive is True
    assert frozprsn.services.kerberos.not_inactive is True
    assert formerpsn.services.kerberos.not_inactive is False

# The library service doesn't really have much to test
def test_library(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the library service
    assert affilite.services.library is None
    assert afilbase.services.library is None
    assert functional.services.library is None
    assert formerpsn.services.library is None
    assert oldfunctional.services.library is None
    assert sharedmailbox.services.library is None

    # These folks should have the library service
    assert fullprsn.services.library is not None
    assert frozprsn.services.library is not None

    # Confirm status is active
    assert fullprsn.services.library.status == ServiceStatus.ACTIVE
    assert frozprsn.services.library.status == ServiceStatus.ACTIVE

# SEAS has lots of attributes that can be present
def test_seas(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the seas service
    assert afilbase.services.seas is None
    assert functional.services.seas is None
    assert formerpsn.services.seas is None
    assert oldfunctional.services.seas is None

    # These folks should have the seas service
    assert fullprsn.services.seas is not None
    assert frozprsn.services.seas is not None
    assert affilite.services.seas is not None
    assert sharedmailbox.services.seas is not None

    # Confirm statuses are active
    assert fullprsn.services.seas.status == ServiceStatus.ACTIVE
    assert frozprsn.services.seas.status == ServiceStatus.ACTIVE
    assert affilite.services.seas.status == ServiceStatus.ACTIVE
    assert sharedmailbox.services.seas.status == ServiceStatus.ACTIVE

    # Check local
    assert fullprsn.services.seas.local == 'fullprsn@onmicrosoft.example.com'
    assert frozprsn.services.seas.local == 'frozprsn@onmicrosoft.example.com'
    assert affilite.services.seas.local == 'affilite@zm88.example.com'
    assert sharedmailbox.services.seas.local is None

    # Each account's username should be in the sunetids list
    assert fullprsn.sunetid in fullprsn.services.seas.sunetid
    assert frozprsn.sunetid in frozprsn.services.seas.sunetid
    assert affilite.sunetid in affilite.services.seas.sunetid
    assert sharedmailbox.sunetid in sharedmailbox.services.seas.sunetid

    # One account has a SUNetID alias, others don't
    assert len(fullprsn.services.seas.sunetid) == 1
    assert 'frozen.person' in frozprsn.services.seas.sunetid
    assert len(affilite.services.seas.sunetid) == 1
    assert len(sharedmailbox.services.seas.sunetid) == 1

    # Each account's preferred sunetid should be in the sunetid list
    assert fullprsn.services.seas.sunetidpreferred in fullprsn.services.seas.sunetid
    assert frozprsn.services.seas.sunetidpreferred in frozprsn.services.seas.sunetid
    assert affilite.services.seas.sunetidpreferred in affilite.services.seas.sunetid
    assert sharedmailbox.services.seas.sunetidpreferred in sharedmailbox.services.seas.sunetid

    # Check URIs - Only one person has a URI
    assert fullprsn.services.seas.urirouteto is None
    assert frozprsn.services.seas.urirouteto == 'http://geocities.com/neworleans/12/11/'
    assert affilite.services.seas.urirouteto is None
    assert sharedmailbox.services.seas.urirouteto is None

# None of the email settings should be used anymore, so we just test status
def test_email(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the email service
    assert afilbase.services.email is None
    assert functional.services.email is None
    assert formerpsn.services.email is None
    assert oldfunctional.services.email is None
    assert sharedmailbox.services.email is None

    # These folks should have the email service
    assert fullprsn.services.email is not None
    assert frozprsn.services.email is not None
    assert affilite.services.email is not None

    # Confirm statuses are active
    assert fullprsn.services.email.status == ServiceStatus.ACTIVE
    assert frozprsn.services.email.status == ServiceStatus.ACTIVE
    assert affilite.services.email.status == ServiceStatus.ACTIVE

# Only two accounts have autoreply turned on
def test_autoreply(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the autoreply service
    assert fullprsn.services.autoreply is None
    assert affilite.services.autoreply is None
    assert afilbase.services.autoreply is None
    assert functional.services.autoreply is None
    assert formerpsn.services.autoreply is None
    assert oldfunctional.services.autoreply is None
    assert sharedmailbox.services.autoreply is None

    # These folks should have the autoreply service
    assert frozprsn.services.autoreply is not None

    # Confirm statuses are active
    assert frozprsn.services.autoreply.status == ServiceStatus.ACTIVE

    # Check forward
    assert frozprsn.services.autoreply.forward == 'frozprsn@forward.example.com'

    # Check subj
    assert frozprsn.services.autoreply.subj == 'Out of office'

    # Check msg
    assert frozprsn.services.autoreply.msg == 'I am currently out of the office.\\r\\nI will respond when I return.'

# All the folks with leland service have the same shell
def test_leland(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the leland service
    assert afilbase.services.leland is None
    assert functional.services.leland is None
    assert oldfunctional.services.leland is None
    assert sharedmailbox.services.leland is None

    # These folks should have the leland service
    assert fullprsn.services.leland is not None
    assert frozprsn.services.leland is not None
    assert formerpsn.services.leland is not None
    assert affilite.services.leland is not None

    # Confirm statuses are active
    assert fullprsn.services.leland.status == ServiceStatus.ACTIVE
    assert frozprsn.services.leland.status == ServiceStatus.ACTIVE
    assert formerpsn.services.leland.status == ServiceStatus.INACTIVE
    assert affilite.services.leland.status == ServiceStatus.ACTIVE

    # Confirm shells are BASH (or not present, which is possible)
    assert fullprsn.services.leland.shell is None
    assert frozprsn.services.leland.shell == '/bin/bash'
    assert formerpsn.services.leland.shell == '/bin/tcsh'
    assert affilite.services.leland.shell == '/bin/bash'

# Full folks have PTS
def test_pts(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the pts service
    assert afilbase.services.pts is None
    assert formerpsn.services.pts is None
    assert oldfunctional.services.pts is None
    assert sharedmailbox.services.pts is None

    # These folks should have the pts service
    assert fullprsn.services.pts is not None
    assert frozprsn.services.pts is not None
    assert affilite.services.pts is not None
    assert functional.services.pts is not None

    # Confirm statuses are active
    assert fullprsn.services.pts.status == ServiceStatus.ACTIVE
    assert frozprsn.services.pts.status == ServiceStatus.ACTIVE
    assert affilite.services.pts.status == ServiceStatus.ACTIVE
    assert functional.services.pts.status == ServiceStatus.ACTIVE

    # Check PTA UID matches Kerberos UID
    assert fullprsn.services.pts.uid == fullprsn.services.kerberos.uid
    assert frozprsn.services.pts.uid == frozprsn.services.kerberos.uid
    assert affilite.services.pts.uid == affilite.services.kerberos.uid
    assert functional.services.pts.uid == functional.services.kerberos.uid

# Folks who have PTS often have AFS
def test_afs(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the afs service
    assert afilbase.services.afs is None
    assert formerpsn.services.afs is None
    assert functional.services.afs is None
    assert oldfunctional.services.afs is None
    assert sharedmailbox.services.afs is None

    # These folks should have the afs service
    assert fullprsn.services.afs is not None
    assert frozprsn.services.afs is not None
    assert affilite.services.afs is not None

    # Confirm statuses are active
    assert fullprsn.services.afs.status == ServiceStatus.ACTIVE
    assert frozprsn.services.afs.status == ServiceStatus.ACTIVE
    assert affilite.services.afs.status == ServiceStatus.ACTIVE

    # Check AFS homedir is as expected
    def afs_homedir(acct: Account) -> str:
        return '/afs/te/users/' + acct.sunetid[0] + '/' + acct.sunetid[1] + '/' + acct.sunetid
    assert fullprsn.services.afs.homedirectory == afs_homedir(fullprsn)
    assert frozprsn.services.afs.homedirectory == afs_homedir(frozprsn)
    assert affilite.services.afs.homedirectory == afs_homedir(affilite)

# No testing is done for the dialin service
def test_dialin(account_client):
    # Fetch our accounts
    fullprsn = account_client['fullprsn']
    frozprsn = account_client['frozprsn']
    formerpsn = account_client['formerpsn']
    affilite = account_client['affilite']
    afilbase = account_client['afilbase']
    functional = account_client['functional']
    oldfunctional = account_client['oldfunctional']
    sharedmailbox = account_client['sharedmailbox']

    # These folks should *not* have the dialin service
    assert frozprsn.services.dialin is None
    assert afilbase.services.dialin is None
    assert formerpsn.services.dialin is None
    assert functional.services.dialin is None
    assert oldfunctional.services.dialin is None
    assert sharedmailbox.services.dialin is None

    # These folks should have the afs service
    assert fullprsn.services.dialin is not None
    assert affilite.services.dialin is not None
