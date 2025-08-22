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

import itertools
import pytest
from stanford.mais.client import MAISClient
from stanford.mais.account import AccountClient, Account


# An AccountClient with no client or a bad client should throw.
def test_badclient():
    with pytest.raises(TypeError):
        AccountClient()
    with pytest.raises(TypeError):
        AccountClient(client='blah')

"""
Account:
- get with non-ASCII raises ValueError
- return 401/403 raises PermissionError
- return 400/500 raises ChildProcessError
- return 404 raises KeyError

Account `nøbødy` shouldn't even make an API call.
Account `nobody` returns a 404
Account `hidden1` returns a 401
Account `hidden3` returns a 403
Account `broken4` returns a 400
Account `broken5` returns a 500
"""
def test_badqueries(account_client):
    with pytest.raises(ValueError):
        ac = account_client['nøbødy']
    with pytest.raises(KeyError):
        ac = account_client['nobody']
    with pytest.raises(PermissionError):
        ac = account_client['hidden1']
    with pytest.raises(PermissionError):
        ac = account_client['hidden3']
    with pytest.raises(ChildProcessError):
        ac = account_client['broken4']
    with pytest.raises(ChildProcessError):
        ac = account_client['broken5']

# Test that the get method and the key-based methods work
# Once we test this, we'll use key-based methods from now on.
def test_get_vs_key(account_client):
    key_result = account_client['fullprsn']
    get_result = Account.get(
        client=account_client,
        sunetid='fullprsn',
    )
    assert key_result is get_result

# Test that looking up a sunetid@stanford.edu works,
# and that looking up an alias doesn't work
def test_sunet_vs_email(account_client):
    sunet_result = account_client['frozprsn']
    email_result = account_client['frozprsn@stanford.edu']
    assert sunet_result is email_result
    with pytest.raises(KeyError):
        result = account_client['frozen.person@stanford.edu']

# Test that support for the `in` keyword workd.
def test_in(account_client):
    assert 'fullprsn' in account_client
    assert 'nobody' not in account_client

# Test clearing the cache works
def test_clear(account_client):
    fullprsn_result1 = account_client['fullprsn']
    account_client.clear_cache()
    fullprsn_result2 = account_client['fullprsn']
    assert fullprsn_result1 is not fullprsn_result2

"""
The next set of tests checks that AccountViews work.  It uses our test users:

'fullprsn',
'frozprsn',
'formerpsn',
'affilite',
'afilbase',
'functional',
'oldfunctional',
'sharedmailbox',
"""


# Test inactive folks cannot be found
def test_only_active(account_client):
    only_active = account_client.only_active()

    assert only_active['fullprsn'].sunetid == 'fullprsn'
    assert only_active['frozprsn'].sunetid == 'frozprsn'
    with pytest.raises(KeyError):
        assert only_active['formerpsn'].sunetid == 'formerpsn'
    assert only_active['affilite'].sunetid == 'affilite'
    assert only_active['afilbase'].sunetid == 'afilbase'
    assert only_active['functional'].sunetid == 'functional'
    with pytest.raises(KeyError):
        assert only_active['oldfunctional'].sunetid == 'oldfunctional'
    assert only_active['sharedmailbox'].sunetid == 'sharedmailbox'

# Test that *active* folks cannot be found
def test_only_inactive(account_client):
    only_inactive = account_client.only_inactive()

    with pytest.raises(KeyError):
        assert only_inactive['fullprsn'].sunetid == 'fullprsn'
    with pytest.raises(KeyError):
        assert only_inactive['frozprsn'].sunetid == 'frozprsn'
    assert only_inactive['formerpsn'].sunetid == 'formerpsn'
    with pytest.raises(KeyError):
        assert only_inactive['affilite'].sunetid == 'affilite'
    with pytest.raises(KeyError):
        assert only_inactive['afilbase'].sunetid == 'afilbase'
    with pytest.raises(KeyError):
        assert only_inactive['functional'].sunetid == 'functional'
    assert only_inactive['oldfunctional'].sunetid == 'oldfunctional'
    with pytest.raises(KeyError):
        assert only_inactive['sharedmailbox'].sunetid == 'sharedmailbox'

# Test functional accounts cannot be found
def test_only_people(account_client):
    only_people = account_client.only_people()

    assert only_people['fullprsn'].sunetid == 'fullprsn'
    assert only_people['frozprsn'].sunetid == 'frozprsn'
    assert only_people['formerpsn'].sunetid == 'formerpsn'
    assert only_people['affilite'].sunetid == 'affilite'
    assert only_people['afilbase'].sunetid == 'afilbase'
    with pytest.raises(KeyError):
        assert only_people['functional'].sunetid == 'functional'
    with pytest.raises(KeyError):
        assert only_people['oldfunctional'].sunetid == 'oldfunctional'
    with pytest.raises(KeyError):
        assert only_people['sharedmailbox'].sunetid == 'sharedmailbox'

# Test that people cannot be found
def test_only_functional(account_client):
    only_functional = account_client.only_functional()

    with pytest.raises(KeyError):
        assert only_functional['fullprsn'].sunetid == 'fullprsn'
    with pytest.raises(KeyError):
        assert only_functional['frozprsn'].sunetid == 'frozprsn'
    with pytest.raises(KeyError):
        assert only_functional['formerpsn'].sunetid == 'formerpsn'
    with pytest.raises(KeyError):
        assert only_functional['affilite'].sunetid == 'affilite'
    with pytest.raises(KeyError):
        assert only_functional['afilbase'].sunetid == 'afilbase'
    assert only_functional['functional'].sunetid == 'functional'
    assert only_functional['oldfunctional'].sunetid == 'oldfunctional'
    assert only_functional['sharedmailbox'].sunetid == 'sharedmailbox'

# Test stacking views: We only want active people
def test_active_people(account_client):
    only_active_people = account_client.only_active().only_people()

    assert only_active_people['fullprsn'].sunetid == 'fullprsn'
    assert only_active_people['frozprsn'].sunetid == 'frozprsn'
    with pytest.raises(KeyError):
        assert only_active_people['formerpsn'].sunetid == 'formerpsn'
    assert only_active_people['affilite'].sunetid == 'affilite'
    assert only_active_people['afilbase'].sunetid == 'afilbase'
    with pytest.raises(KeyError):
        assert only_active_people['functional'].sunetid == 'functional'
    with pytest.raises(KeyError):
        assert only_active_people['oldfunctional'].sunetid == 'oldfunctional'
    with pytest.raises(KeyError):
        assert only_active_people['sharedmailbox'].sunetid == 'sharedmailbox'

# Active *and* inactive?  Nobody should be found, then.
def test_nobody_1(account_client):
    only_nobody_1 = account_client.only_active().only_inactive()

    with pytest.raises(KeyError):
        assert only_nobody_1['fullprsn'].sunetid == 'fullprsn'
    with pytest.raises(KeyError):
        assert only_nobody_1['frozprsn'].sunetid == 'frozprsn'
    with pytest.raises(KeyError):
        assert only_nobody_1['formerpsn'].sunetid == 'formerpsn'
    with pytest.raises(KeyError):
        assert only_nobody_1['affilite'].sunetid == 'affilite'
    with pytest.raises(KeyError):
        assert only_nobody_1['afilbase'].sunetid == 'afilbase'
    with pytest.raises(KeyError):
        assert only_nobody_1['functional'].sunetid == 'functional'
    with pytest.raises(KeyError):
        assert only_nobody_1['oldfunctional'].sunetid == 'oldfunctional'
    with pytest.raises(KeyError):
        assert only_nobody_1['sharedmailbox'].sunetid == 'sharedmailbox'

# People *and* functional?  Nobody should be found, then.
def test_nobody_2(account_client):
    only_nobody_2 = account_client.only_people().only_functional()

    with pytest.raises(KeyError):
        assert only_nobody_2['fullprsn'].sunetid == 'fullprsn'
    with pytest.raises(KeyError):
        assert only_nobody_2['frozprsn'].sunetid == 'frozprsn'
    with pytest.raises(KeyError):
        assert only_nobody_2['formerpsn'].sunetid == 'formerpsn'
    with pytest.raises(KeyError):
        assert only_nobody_2['affilite'].sunetid == 'affilite'
    with pytest.raises(KeyError):
        assert only_nobody_2['afilbase'].sunetid == 'afilbase'
    with pytest.raises(KeyError):
        assert only_nobody_2['functional'].sunetid == 'functional'
    with pytest.raises(KeyError):
        assert only_nobody_2['oldfunctional'].sunetid == 'oldfunctional'
    with pytest.raises(KeyError):
        assert only_nobody_2['sharedmailbox'].sunetid == 'sharedmailbox'
