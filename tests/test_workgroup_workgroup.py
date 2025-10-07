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
import sys
import time
from stanford.mais.client import MAISClient
from stanford.mais.workgroup import Workgroup, WorkgroupClient, WorkgroupDeleted, WorkgroupFilter, WorkgroupVisibility


"""
This script tests parts of Workgroup that are not tested elsewhere.  A
collection of miscellaneous tests.
"""

# Test manually instantiating a Workgroup fails
def test_badworkgroup(workgroup_client):
    with pytest.raises(NotImplementedError):
        Workgroup(client=workgroup_client)

# Test that fetching a workgroup handles a stale cache entry
# On non-CPython platforms, skip this test.  Why?  See below.
@pytest.mark.skipif(
    sys.implementation.name != 'cpython',
    reason='Test requires CPython'
)
def test_get_refetch(workgroup_client):
    # First, fetch the workgroup as normal
    result1 = workgroup_client['test:1']
    result1_last_update = result1.last_update
    result1_name = result1.name
    result1_description = result1.description
    result1_filter = result1.filter
    result1_privgroup = result1.privgroup
    result1_reusable = result1.reusable
    result1_visibility = result1.visibility
    result1_member_people = set(result1.members.people)
    result1_member_workgroups = set(result1.members.workgroups)
    result1_member_certs = set(result1.members.certificates)
    result1_admin_people = set(result1.administrators.people)
    result1_admin_workgroups = set(result1.administrators.workgroups)
    result1_admin_certs = set(result1.administrators.certificates)

    # Deleting result1 (which is a ref to an instance) should cause Workgroup
    # instance's referene count to drop to zero, triggering a deletion.
    # NOTE: This depends on CPython behavior, which garbage-collects an object
    # as soon as its reference count drops to zero.
    del result1

    # Test the weakref that's still in the cache, to confirm it's gone.
    assert workgroup_client._cache['test:1']() is None

    # Re-fetch the workgroup to reload it, then compare
    result2 = workgroup_client['test:1']
    assert result1_last_update == result2.last_update
    assert result1_name == result2.name
    assert result1_description == result2.description
    assert result1_filter == result2.filter
    assert result1_privgroup == result2.privgroup
    assert result1_reusable == result2.reusable
    assert result1_visibility == result2.visibility
    assert result1_member_people == set(result2.members.people)
    assert result1_member_workgroups == set(result2.members.workgroups)
    assert result1_member_certs == set(result2.members.certificates)
    assert result1_admin_people == set(result2.administrators.people)
    assert result1_admin_workgroups == set(result2.administrators.workgroups)
    assert result1_admin_certs == set(result2.administrators.certificates)

# Test for the rare case of a workgroup without a description field
def test_get_no_description(workgroup_client):
    result = workgroup_client['test:2']
    assert result.description == ''

# Test refreshing a workgroup works
def test_refresh(workgroup_client):
    # First, fetch the workgroup as normal
    result1 = workgroup_client['test:1']
    result1_last_update = result1.last_update
    result1_name = result1.name
    result1_description = result1.description
    result1_filter = result1.filter
    result1_privgroup = result1.privgroup
    result1_reusable = result1.reusable
    result1_visibility = result1.visibility
    result1_member_people = set(result1.members.people)
    result1_member_workgroups = set(result1.members.workgroups)
    result1_member_certs = set(result1.members.certificates)
    result1_admin_people = set(result1.administrators.people)
    result1_admin_workgroups = set(result1.administrators.workgroups)
    result1_admin_certs = set(result1.administrators.certificates)

    # Mess with the instance
    # NOTE: Skip mess with the name, as this breaks refresh
    result1._last_update = datetime.datetime.now()
    result1._description = 'blah'
    result1._privgroup = False
    result1._filter = WorkgroupFilter.STAFF
    result1._reusable = False
    result1._visibility = WorkgroupVisibility.PRIVATE
    result1.members.people._identifiers = {'nobody'}
    result1.members.workgroups._identifiers = {'super:owners'}
    result1.members.certificates._identifiers = {'root-cert'}
    result1.administrators.people._identifiers = {'nobody'}
    result1.administrators.workgroups._identifiers = {'super:owners'}
    result1.administrators.certificates._identifiers = {'root-cert'}

    # Make sure things do *not* match
    assert result1_last_update != result1.last_update
    assert result1_description != result1.description
    assert result1_filter != result1.filter
    assert result1_privgroup != result1.privgroup
    assert result1_reusable != result1.reusable
    assert result1_visibility != result1.visibility
    assert result1_member_people != set(result1.members.people)
    assert result1_member_workgroups != set(result1.members.workgroups)
    assert result1_member_certs != set(result1.members.certificates)
    assert result1_admin_people != set(result1.administrators.people)
    assert result1_admin_workgroups != set(result1.administrators.workgroups)
    assert result1_admin_certs != set(result1.administrators.certificates)

    # Refresh the workgroup
    result1.refresh()

    # Make sure things are what we expect
    assert result1_last_update == result1.last_update
    assert result1_name == result1.name
    assert result1_description == result1.description
    assert result1_privgroup == result1.privgroup
    assert result1_filter == result1.filter
    assert result1_reusable == result1.reusable
    assert result1_visibility == result1.visibility
    assert result1_member_people == set(result1.members.people)
    assert result1_member_workgroups == set(result1.members.workgroups)
    assert result1_member_certs == set(result1.members.certificates)
    assert result1_admin_people == set(result1.administrators.people)
    assert result1_admin_workgroups == set(result1.administrators.workgroups)
    assert result1_admin_certs == set(result1.administrators.certificates)

# Test refreshing a workgroup, which has been deleted behind us, works
def test_refresh_deleted(workgroup_client):
    # Fetch test:1, then change its name and refresh
    result2 = workgroup_client['test:1']
    result2._name = 'test:inactive'

    # Refreshing should raise an exception
    with pytest.raises(WorkgroupDeleted):
        result2.refresh()

    # The refreshed workgroup should be deleted
    assert result2.deleted is True

# Test handling of upstream errors during workgroup refresh
def test_refresh_errors(workgroup_client):
    # Fetch test:1, then change its name and refresh
    result3 = workgroup_client['test:1']
    result3._name = 'bad:w1'
    with pytest.raises(ChildProcessError):
        result3.refresh()

    # NOTE: Clear the client cache before fetching again!
    workgroup_client.clear_cache()
    result4 = workgroup_client['test:1']
    result4._name = 'bad:w3'
    with pytest.raises(PermissionError):
        result4.refresh()

    # Test a weird response code on refresh
    workgroup_client.clear_cache()
    result5 = workgroup_client['test:1']
    result5._name = 'bad:w6'
    with pytest.raises(NotImplementedError):
        result5.refresh()

# Test the last_refresh time is valid
def test_last_refresh(workgroup_client):
    # Fetch the workgroup & get the time
    result = workgroup_client['test:1']
    now1 = datetime.datetime.now(tz=datetime.timezone.utc)

    # There should be a <1 second difference
    last_refresh1 = result.last_refresh
    diff1 = last_refresh1 - now1
    assert abs(diff1.total_seconds()) <= 1

    # Wait two seconds, then refresh
    time.sleep(2)
    result.refresh()
    now2 = datetime.datetime.now(tz=datetime.timezone.utc)

    # Check we actually refreshed, and we have a <1 second difference
    last_refresh2 = result.last_refresh
    diff2 = last_refresh2 - now2
    assert last_refresh1 != last_refresh2
    assert abs(diff2.total_seconds()) <= 1

# Test deletion works, and that accessing a deleted workgroup raises exceptions
def test_delete(workgroup_client):
    result = workgroup_client['test:1']
    last_refresh = result.last_refresh

    # Check is_deleted before and after deletion
    assert result.deleted is False
    result.delete()
    assert result.deleted is True

    # Check a few other properties that are still accessible after deletion
    assert result.client is workgroup_client
    assert result.name == 'test:1'
    assert result.last_refresh != last_refresh

    # Check other properties raise an exception after deletion
    with pytest.raises(EOFError):
        result.description
    with pytest.raises(EOFError):
        result.privgroup
    with pytest.raises(EOFError):
        result.reusable
    with pytest.raises(EOFError):
        result.visibility
    with pytest.raises(EOFError):
        result.filter
    with pytest.raises(EOFError):
        result.members
    with pytest.raises(EOFError):
        result.administrators
    with pytest.raises(EOFError):
        result.last_update
    with pytest.raises(EOFError):
        result.can_see_membership

    # Trying to get privgroup should raise an exception
    with pytest.raises(EOFError):
        result.get_privgroup()

    # Trying to delete again, or to refresh, should raise an exception
    with pytest.raises(EOFError):
        result.delete()
    with pytest.raises(EOFError):
        result.refresh()

    # Trying to update anything should raise an exception
    with pytest.raises(EOFError):
        result._update('description', 'x')
    with pytest.raises(EOFError):
        result.description = 'x'
    with pytest.raises(EOFError):
        result.privgroup = False
    with pytest.raises(EOFError):
        result.reusable = False
    with pytest.raises(EOFError):
        result.visibility = WorkgroupVisibility.PRIVATE
    with pytest.raises(EOFError):
        result.filter = WorkgroupFilter.FACULTY
    with pytest.raises(EOFError):
        result.members.people.add('nmckenna')
    with pytest.raises(EOFError):
        result.administrators.people.add('nmckenna')

# A few workgroups are mocked to trigger upstream errors on deletion
def test_delete_error(workgroup_client):
    result_owners = workgroup_client['workgroup:test-owners']
    with pytest.raises(ChildProcessError):
        result_owners.delete()

    result_private = workgroup_client['private:1']
    with pytest.raises(PermissionError):
        result_private.delete()

    result_deleted = workgroup_client['test:1']
    result_deleted._name = 'test:inactive'
    with pytest.raises(WorkgroupDeleted):
        result_deleted.delete()

    workgroup_client.clear_cache()
    result_deleted = workgroup_client['test:1']
    result_deleted._name = 'bad:521'
    with pytest.raises(NotImplementedError):
        result_deleted.delete()

    # TODO: handle 500 error

# Test if our "can we see membership?" test works
def test_can_see_membership(workgroup_client):
    result = workgroup_client['private:1']

    # We shouldn't see any members or administrators
    assert len(result.members) == 0
    assert len(result.administrators) == 0

    # Workgroup should be private, and can_see_membership should be False
    assert result.visibility == WorkgroupVisibility.PRIVATE
    assert result.can_see_membership is False

# Test if repr works as expected
def test_repr(workgroup_client):
    # Check some repr()s
    assert repr(workgroup_client['test:1']) == 'Workgroup(name="test:1",description="Test 1",visibility=STANFORD,reusable=True,privgroup=True,filter=NONE,members=WorkgroupMembership(people={\'akkornel\'}),administrators=WorkgroupMembership(people={\'stanford\'},workgroups={\'workgroup:test-owners\'}),last_update=2025-01-01)'

    # Check again, after workgroup deletion
    result = workgroup_client['test:1']
    result.delete()
    assert repr(result) == 'Workgroup(deleted)'

# Test that bad date-strings trigger an exception
def test_datestr(workgroup_client):
    with pytest.raises(ValueError):
        Workgroup.datestr_to_date('JAN-2020')
    with pytest.raises(ValueError):
        Workgroup.datestr_to_date('01-KARL-2020')
    with pytest.raises(ValueError):
        Workgroup.datestr_to_date('01-JMB-2022')
