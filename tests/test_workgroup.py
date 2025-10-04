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
from stanford.mais.workgroup import WorkgroupClient, WorkgroupDeleted, Workgroup


"""
This file tests things implemented by the WorkgroupClient class, and also (as a
result) ends up testing basic Workgroup.get() functionality.
"""


# A WorkgroupClient with no client or a bad client should throw.
def test_badclient():
    with pytest.raises(TypeError):
        WorkgroupClient()
    with pytest.raises(TypeError):
        WorkgroupClient(client='blah')

"""
Workgroup:
- return 400/500 raises ChildProcessError
- return 401/403 raises PermissionError
- return 404 raises KeyError

Workgroup `bad:w1` returns a 400
Workgroup `bad:w2` returns a 500
Workgroup `bad:w3` returns a 401
Workgroup `bad:w4` returns a 403
Workgroup `bad:w5` returns a 404
Workgroup `test:inactive` returns a special 400 for an inactive workgroup
"""
def test_badqueries(workgroup_client):
    with pytest.raises(ChildProcessError):
        wc = workgroup_client['bad:w1']
    with pytest.raises(ChildProcessError):
        wc = workgroup_client['bad:w2']
    with pytest.raises(PermissionError):
        wc = workgroup_client['bad:w3']
    with pytest.raises(PermissionError):
        wc = workgroup_client['bad:w4']
    with pytest.raises(KeyError):
        wc = workgroup_client['bad:w5']
    with pytest.raises(NotImplementedError):
        wc = workgroup_client['bad:w6']
    with pytest.raises(KeyError):
        wc = workgroup_client['test:inactive']
    with pytest.raises(WorkgroupDeleted):
        wc = workgroup_client['test:inactive']

# Test that the get method and the key-based methods work
# Once we test this, we'll use the key-based methods from now on.
def test_get_vs_key(workgroup_client):
    key_result = workgroup_client['test:1']
    get_result = Workgroup.get(
        client=workgroup_client,
        name='test:1',
    )
    assert key_result is get_result

# Test that support for the `in` keyword works
def test_in(workgroup_client):
    assert 'test:1' in workgroup_client
    assert 'bad:w5' not in workgroup_client

# Test we can access ourselves through the workgroup
def test_client(workgroup_client):
    result = workgroup_client['test:1']
    assert result.client is workgroup_client

# Test a search that returns no results
def test_search_empty(workgroup_client):
    results = workgroup_client.search_by_name('noresults:*')
    assert len(results) == 0

# Test a search that returns results
def test_search_by_name(workgroup_client):
    results = workgroup_client.search_by_name('test:*')

    # Check we got the correct number of results
    assert len(results) == 1

    # For each returned workgroup, check it can load the full workgroup, and
    # that things match.
    for result in results:
        full_result = result.workgroup(workgroup_client)

        assert result.name == full_result.name
        assert result.description == full_result.description
        assert result.last_update == full_result.last_update

# Test invalid searches by name
def test_search_by_name_bad(workgroup_client):
    with pytest.raises(ValueError):
        workgroup_client.search_by_name('')
    with pytest.raises(ValueError):
        workgroup_client.search_by_name('*')
    with pytest.raises(ChildProcessError):
        workgroup_client.search_by_name('bad:w1')
    with pytest.raises(PermissionError):
        workgroup_client.search_by_name('bad:w3')
    with pytest.raises(NotImplementedError):
        workgroup_client.search_by_name('bad:w6')

# Search for member user
def test_search_by_member_user(workgroup_client):
    results = workgroup_client.search_by_user('akkornel')

    # Check we got one result, and that it matches what we expect
    assert len(results.is_member) == 1
    assert len(results.is_administrator) == 0
    result = list(results.is_member)[0]
    assert result.name == 'test:1'
    assert result.description == 'Test 1'
    assert result.last_update.year == 2025
    assert result.last_update.month == 1
    assert result.last_update.day == 1

# Search for member workgroup
def test_search_by_member_workgroup(workgroup_client):
    results = workgroup_client.search_by_workgroup('workgroup:test-owners')

    # Check we got one result, and that it matches what we expect
    assert len(results.is_member) == 0
    assert len(results.is_administrator) == 1
    result = list(results.is_administrator)[0]
    assert result.name == 'test:1'
    assert result.description == 'Test 1'
    assert result.last_update.year == 2025
    assert result.last_update.month == 1
    assert result.last_update.day == 1

# Search for member certificate
def test_search_by_member_cert(workgroup_client):
    results = workgroup_client.search_by_certificate('client-cert-1')

    # Check we got one result, and that it matches what we expect
    assert len(results.is_member) == 0
    assert len(results.is_administrator) == 1
    result = list(results.is_administrator)[0]
    assert result.name == 'workgroup:test-owners'
    assert result.description == 'Workgroup stem for testing'
    assert result.last_update.year == 2025
    assert result.last_update.month == 1
    assert result.last_update.day == 1

# Do a few bad search-by-X calls
def test_search_by_bad(workgroup_client):
    with pytest.raises(ValueError):
        workgroup_client.search_by_user('')
    with pytest.raises(ValueError):
        workgroup_client.search_by_workgroup('')
    with pytest.raises(ValueError):
        workgroup_client.search_by_certificate('')
    with pytest.raises(ChildProcessError):
        workgroup_client.search_by_certificate('bad400')
    with pytest.raises(PermissionError):
        workgroup_client.search_by_certificate('bad401')
    with pytest.raises(NotImplementedError):
        workgroup_client.search_by_certificate('bad521')

# Search for a certificate that does not exist
def test_search_by_member_cert_empty(workgroup_client):
    results = workgroup_client.search_by_certificate('nonexistant')

    # Check we got zero results
    assert len(results.is_member) == 0
    assert len(results.is_administrator) == 0

# Test clearing the cache works
def test_clear(workgroup_client):
    wg1_result1 = workgroup_client['test:1']
    workgroup_client.clear_cache()
    wg1_result2 = workgroup_client['test:1']
    assert wg1_result1 is not wg1_result2
