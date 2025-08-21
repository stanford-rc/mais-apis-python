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
