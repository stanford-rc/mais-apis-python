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
import sys
from stanford.mais.client import MAISClient
from stanford.mais.workgroup import WorkgroupClient, Workgroup, WorkgroupDeleted


"""
This script tests all of the Workgroup membership-related methods.
"""


# Check collection type is correct
def test_collection_type(workgroup_client):
    workgroup = workgroup_client['test:1']

    assert workgroup.members.people.collection_type == 'members'
    assert workgroup.members.workgroups.collection_type == 'members'
    assert workgroup.members.certificates.collection_type == 'members'
    assert workgroup.administrators.people.collection_type == 'administrators'
    assert workgroup.administrators.workgroups.collection_type == 'administrators'
    assert workgroup.administrators.certificates.collection_type == 'administrators'

# Check that each container maps back to its workgroup
# On non-CPython platforms, skip this test.  Why?  See below.
@pytest.mark.skipif(
    sys.implementation.name != 'cpython',
    reason='Test requires CPython'
)
def test_collection_linkage(workgroup_client):
    workgroup = workgroup_client['test:1']

    # Copy container refs into our own variables
    members = workgroup.members
    members_people = members.people
    members_workgroups = members.workgroups
    members_certificates = members.certificates
    admins = workgroup.administrators
    admins_people = admins.people
    admins_workgroups = admins.workgroups
    admins_certificates = admins.certificates

    # Make sure the linkage exists
    assert members_people.workgroup is workgroup
    assert members_workgroups.workgroup is workgroup
    assert members_certificates.workgroup is workgroup
    assert admins_people.workgroup is workgroup
    assert admins_workgroups.workgroup is workgroup
    assert admins_certificates.workgroup is workgroup

    # Delete the reference to the workgroup, and clear the cache This should
    # cause Workgroup instance's referene count to drop to zero, triggering a
    # deletion.
    # NOTE: This depends on CPython behavior, which garbage-collects an object
    # as soon as its reference count drops to zero.
    del workgroup
    workgroup_client.clear_cache()

    # Make sure the linkage is broken
    assert members_people.workgroup is None
    assert members_workgroups.workgroup is None
    assert members_certificates.workgroup is None
    assert admins_people.workgroup is None
    assert admins_workgroups.workgroup is None
    assert admins_certificates.workgroup is None

    # Add & delete should raise EOFError
    with pytest.raises(EOFError):
        admins.update_from_upstream([
            dict(),
            dict(),
            dict(),
        ])
    with pytest.raises(EOFError):
        members_people.add('epoch')
    with pytest.raises(EOFError):
        members_people.remove('akkornel')

    # Updating a specific set should work
    members_people.update_from_upstream(set())

# Test iteration works
def test_iteration(workgroup_client):
    workgroup = workgroup_client['test:1']

    # This is who we expect to see in members & administrators
    expected_members = {
        'akkornel'
    }
    expected_admins = {
        'stanford',
        'workgroup:test-owners',
    }

    # For each of members and administrators, go through all of the containers.
    # If we find an identifier that we do not expect, alert.
    for member_type in (
        workgroup.members.people,
        workgroup.members.workgroups,
        workgroup.members.certificates,
    ):
        for member in member_type:
            assert member in expected_members
            expected_members.remove(member)

    for administrator_type in (
        workgroup.administrators.people,
        workgroup.administrators.workgroups,
        workgroup.administrators.certificates,
    ):
        for administrator in administrator_type:
            assert administrator in expected_admins
            expected_admins.remove(administrator)

    # If we missed any expected admins or members, alert.
    assert len(expected_members) == 0
    assert len(expected_admins) == 0

# Test contains and length
def test_contains_length(workgroup_client):
    workgroup = workgroup_client['test:1']

    # Check lengths
    assert len(workgroup.members) == 1
    assert len(workgroup.members.people) == 1
    assert len(workgroup.members.workgroups) == 0
    assert len(workgroup.members.certificates) == 0

    assert len(workgroup.administrators) == 2
    assert len(workgroup.administrators.people) == 1
    assert len(workgroup.administrators.workgroups) == 1
    assert len(workgroup.administrators.certificates) == 0

    # Check members via 'in'
    assert 'akkornel' in workgroup.members.people
    assert 'akkornel' not in workgroup.administrators.people

    assert 'stanford' in workgroup.administrators.people
    assert 'workgroup:test-owners' in workgroup.administrators.workgroups

    # 'in' also works with Workgroup and PartialWorkgroup
    test_owners_workgroup = workgroup_client['workgroup:test-owners']
    assert test_owners_workgroup in workgroup.administrators.workgroups

    test_results = workgroup_client.search_by_name('workgroup:*')
    assert len(test_results) == 2

# Test a workgroup with an unknown member type
def test_unknown_type(workgroup_client):
    with pytest.raises(NotImplementedError):
        workgroup_client['bad:unknown-type']

# Test adding a user, which is pretty basic
def test_add_user(workgroup_client):
    workgroup = workgroup_client['test:1']

    assert 'adamhl' not in workgroup.members.people
    assert 'adamhl' not in workgroup.administrators.people
    workgroup.members.people.add('adamhl')
    workgroup.administrators.people.add('adamhl')
    assert 'adamhl' in workgroup.members.people
    assert 'adamhl' in workgroup.administrators.people

# Test adding a workgroup, which is pretty complex
def test_add_workgroup(workgroup_client):
    # For each test here, we'll make a workgroup outside of the 'test:' stem.
    # Then, we'll add workgroup:test-owners.
    # At the end, we'll clear cache and try a different way.
    # (Adding works by name, or with a Workgroup or PartialWorkgroup)

    # Test adding by string
    workgroup = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
    )
    assert 'workgroup:test-owners' not in workgroup.administrators.workgroups
    workgroup.administrators.workgroups.add('workgroup:test-owners')
    assert 'workgroup:test-owners' in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test adding by Workgroup
    test_owners_workgroup = workgroup_client['workgroup:test-owners']
    workgroup = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
    )
    assert 'workgroup:test-owners' not in workgroup.administrators.workgroups
    assert test_owners_workgroup not in workgroup.administrators.workgroups
    workgroup.administrators.workgroups.add(test_owners_workgroup)
    assert 'workgroup:test-owners' in workgroup.administrators.workgroups
    assert test_owners_workgroup in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test adding by PartialWorkgroup
    # NOTE: Our conditional pop might not get executed, depending on the
    # randomness of sets.  So, exclude the line from coverage.
    test_results = workgroup_client.search_by_name('workgroup:*')
    assert len(test_results) == 2
    test_result = test_results.pop()
    if test_result.name != 'workgroup:test-owners':
        test_result = test_results.pop() # pragma: no cover
    workgroup = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
    )
    assert 'workgroup:test-owners' not in workgroup.administrators.workgroups
    assert test_result not in workgroup.administrators.workgroups
    workgroup.administrators.workgroups.add(test_result)
    assert 'workgroup:test-owners' in workgroup.administrators.workgroups
    assert test_result in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

# Test adding a certificate
def test_add_certificate(workgroup_client):
    workgroup = workgroup_client['test:1']

    assert 'cert5225' not in workgroup.members.certificates
    assert 'cert5225' not in workgroup.administrators.certificates
    workgroup.members.certificates.add('cert5225')
    workgroup.administrators.certificates.add('cert5225')
    assert 'cert5225' in workgroup.members.certificates
    assert 'cert5225' in workgroup.administrators.certificates

# Test for workgroup-add exceptions
def test_add_bad(workgroup_client):
    workgroup = workgroup_client['test:1']

    # Try adding a non-existant person
    with pytest.raises(ValueError):
        workgroup.members.people.add('nobody')

    # Try adding an identifier that (unknown to us) was already added
    with pytest.raises(KeyError):
        workgroup.members.people.add('leland')

    # Adding an identifier that we already know was added
    with pytest.raises(KeyError):
        workgroup.administrators.people.add('stanford')

    # Try adding some special people to trigger API errors
    with pytest.raises(ChildProcessError):
        workgroup.members.people.add('bad400')
    with pytest.raises(PermissionError):
        workgroup.members.people.add('bad401')
    with pytest.raises(ChildProcessError):
        workgroup.members.people.add('bad500')
    with pytest.raises(NotImplementedError):
        workgroup.members.people.add('bad521')

    # Testing for a inactive workgroup needs to be last, since it marks the
    # entire workgroup as deleted.
    with pytest.raises(WorkgroupDeleted):
        workgroup.members.people.add('inactive')

# Test removing a user
def test_remove_user(workgroup_client):
    # We can remove with the remove operation
    workgroup = workgroup_client['test:1']
    assert 'akkornel' in workgroup.members.people
    assert 'stanford' in workgroup.administrators.people
    workgroup.members.people.remove('akkornel')
    workgroup.administrators.people.remove('stanford')
    assert 'akkornel' not in workgroup.members.people
    assert 'stanford' not in workgroup.administrators.people
    workgroup_client.clear_cache()

    # We can also use del
    workgroup = workgroup_client['test:1']
    assert 'akkornel' in workgroup.members.people
    assert 'stanford' in workgroup.administrators.people
    del workgroup.members.people['akkornel']
    del workgroup.administrators.people['stanford']
    assert 'akkornel' not in workgroup.members.people
    assert 'stanford' not in workgroup.administrators.people
    workgroup_client.clear_cache()

# Test removing a workgroup
def test_remove_workgroup(workgroup_client):
    # We have to test removing by name (as a str), by Workgroup, and by
    # PartialWorkgroup.  We also have to test the .remove() method and `del`.

    # Test removing by name
    workgroup = workgroup_client['workgroup:test-owners']
    assert 'workgroup:workgroup-owners' in workgroup.administrators.workgroups
    workgroup.administrators.workgroups.remove('workgroup:workgroup-owners')
    assert 'workgroup:workgroup-owners' not in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test removing by name with del
    workgroup = workgroup_client['workgroup:test-owners']
    assert 'workgroup:workgroup-owners' in workgroup.administrators.workgroups
    del workgroup.administrators.workgroups['workgroup:workgroup-owners']
    assert 'workgroup:workgroup-owners' not in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test removing by Workgroup
    workgroup = workgroup_client['workgroup:test-owners']
    test_result = workgroup_client['workgroup:workgroup-owners']
    assert test_result in workgroup.administrators.workgroups
    assert 'workgroup:workgroup-owners' in workgroup.administrators.workgroups
    workgroup.administrators.workgroups.remove(test_result)
    assert 'workgroup:workgroup-owners' not in workgroup.administrators.workgroups
    assert test_result not in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test removing by Workgroup with del
    workgroup = workgroup_client['workgroup:test-owners']
    test_result = workgroup_client['workgroup:workgroup-owners']
    assert test_result in workgroup.administrators.workgroups
    assert 'workgroup:workgroup-owners' in workgroup.administrators.workgroups
    del workgroup.administrators.workgroups[test_result]
    assert 'workgroup:workgroup-owners' not in workgroup.administrators.workgroups
    assert test_result not in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test removing by PartialWorkgroup
    workgroup = workgroup_client['workgroup:test-owners']
    test_results = workgroup_client.search_by_name('workgroup:*')
    assert len(test_results) == 2
    test_result = test_results.pop()
    if test_result.name != 'workgroup:workgroup-owners':
        test_result = test_results.pop()
    assert test_result in workgroup.administrators.workgroups
    assert 'workgroup:workgroup-owners' in workgroup.administrators.workgroups
    workgroup.administrators.workgroups.remove(test_result)
    assert 'workgroup:workgroup-owners' not in workgroup.administrators.workgroups
    assert test_result not in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

    # Test removing by PartialWorkgroup with del
    workgroup = workgroup_client['workgroup:test-owners']
    test_results = workgroup_client.search_by_name('workgroup:*')
    assert len(test_results) == 2
    test_result = test_results.pop()
    if test_result.name != 'workgroup:workgroup-owners':
        test_result = test_results.pop()
    assert test_result in workgroup.administrators.workgroups
    assert 'workgroup:workgroup-owners' in workgroup.administrators.workgroups
    del workgroup.administrators.workgroups[test_result]
    assert 'workgroup:workgroup-owners' not in workgroup.administrators.workgroups
    assert test_result not in workgroup.administrators.workgroups
    workgroup_client.clear_cache()

# Test removing a certificate
def test_remove_certificate(workgroup_client):
    # We can remove with the remove operation
    workgroup = workgroup_client['workgroup:test-owners']
    assert 'client-cert-1' in workgroup.members.certificates
    workgroup.members.certificates.remove('client-cert-1')
    assert 'client-cert-1' not in workgroup.members.certificates
    workgroup_client.clear_cache()

    # We can also use del
    workgroup = workgroup_client['workgroup:test-owners']
    assert 'client-cert-1' in workgroup.members.certificates
    del workgroup.members.certificates['client-cert-1']
    assert 'client-cert-1' not in workgroup.members.certificates
    workgroup_client.clear_cache()

# Test for workgroup-remove exceptions
def test_remove_bad(workgroup_client):
    workgroup = workgroup_client['test:1']

    # Internally add a few identifiers for testing
    workgroup.members.people._identifiers |= {
        'bad400',
        'bad401',
        'bad500',
        'bad521',
        'inactive',
    }

    # Attempting to *discard* (not remove) something that's not already in the
    # set, would generate a 404 upstream, but the exception should *not* make
    # it through to us.
    workgroup.administrators.workgroups.discard('workgroup:test-owners')

    # Try removing some special people to trigger API errors
    with pytest.raises(ChildProcessError):
        workgroup.members.people.remove('bad400')
    with pytest.raises(PermissionError):
        workgroup.members.people.remove('bad401')
    with pytest.raises(ChildProcessError):
        workgroup.members.people.remove('bad500')
    with pytest.raises(NotImplementedError):
        workgroup.members.people.remove('bad521')

    # Testing for a inactive workgroup needs to be last, since it marks the
    # entire workgroup as deleted.
    with pytest.raises(WorkgroupDeleted):
        workgroup.members.people.remove('inactive')
