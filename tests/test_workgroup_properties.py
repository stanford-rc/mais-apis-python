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
from stanford.mais.workgroup import WorkgroupClient, Workgroup, WorkgroupDeleted, WorkgroupFilter, WorkgroupVisibility


"""
This script tests that changes to Workgroup properties behave as expected.
"""


# Workgroup name is read-only
def test_name(workgroup_client):
    result = workgroup_client['test:1']
    assert result.name == 'test:1'

    # Changing the name should fail
    with pytest.raises(AttributeError):
        result.name = 'test:2'

# Test description
def test_description(workgroup_client):
    result = workgroup_client['test:1']
    assert result.description == 'Test 1'

    # Test changing description, including a Latin1 character
    result.description = ('x' * 254) + '¿'
    assert result.description == ('x' * 254) + '¿'

    # Too-short or Too-long descriptions should fail
    with pytest.raises(IndexError):
        result.description = ''
    with pytest.raises(IndexError):
        result.description = ('x' * 256)

    # Descriptions with non-Latin1 or invisible characters should fail
    with pytest.raises(ValueError):
        result.description = '€'
    with pytest.raises(ValueError):
        result.description = '\t'

    # As a special test, changing the description to "deleted" should raise a
    # WorkgroupDeleted exception.
    with pytest.raises(WorkgroupDeleted):
        result.description = 'delete'

# Use special descriptions to test upstream failures
def test_upstream(workgroup_client):
    result = workgroup_client['test:1']

    with pytest.raises(ChildProcessError):
        result.description = 'bad1'
    with pytest.raises(ChildProcessError):
        result.description = 'bad2'
    with pytest.raises(PermissionError):
        result.description = 'bad3'
    with pytest.raises(PermissionError):
        result.description = 'bad4'
    with pytest.raises(NotImplementedError):
        result.description = '521'

# Test filter
def test_filter(workgroup_client):
    result = workgroup_client['test:1']
    assert result.filter == WorkgroupFilter.NONE

    # Test each filter value works
    result.filter = WorkgroupFilter.ACADEMIC_ADMINISTRATIVE
    assert result.filter == WorkgroupFilter.ACADEMIC_ADMINISTRATIVE
    
    result.filter = WorkgroupFilter.STUDENT
    assert result.filter == WorkgroupFilter.STUDENT
    
    result.filter = WorkgroupFilter.FACULTY
    assert result.filter == WorkgroupFilter.FACULTY
    
    result.filter = WorkgroupFilter.STAFF
    assert result.filter == WorkgroupFilter.STAFF
    
    result.filter = WorkgroupFilter.FACULTY_STAFF
    assert result.filter == WorkgroupFilter.FACULTY_STAFF
    
    result.filter = WorkgroupFilter.FACULTY_STUDENT
    assert result.filter == WorkgroupFilter.FACULTY_STUDENT
    
    result.filter = WorkgroupFilter.STAFF_STUDENT
    assert result.filter == WorkgroupFilter.STAFF_STUDENT
    
    result.filter = WorkgroupFilter.FACULTY_STAFF_STUDENT
    assert result.filter == WorkgroupFilter.FACULTY_STAFF_STUDENT
    
    result.filter = WorkgroupFilter.NONE
    assert result.filter == WorkgroupFilter.NONE

    # Check an invalid filter string
    with pytest.raises(ValueError):
        result.filter = 'bsdf'

# Test privgroup
def test_privgroup(workgroup_client):
    result = workgroup_client['test:1']
    assert result.privgroup == True

    # Test changing privgroup works
    result.privgroup = False
    assert result.privgroup == False

    result.privgroup = True
    assert result.privgroup == True

    # Test a non-bool
    with pytest.raises(TypeError):
        result.privgroup = 'blah'

# Test reusable
def test_reusable(workgroup_client):
    result = workgroup_client['test:1']
    assert result.reusable == True

    # Test changing reusable works
    result.reusable = False
    assert result.reusable == False

    result.reusable = True
    assert result.reusable == True

    # Test a non-bool
    with pytest.raises(TypeError):
        result.reusable = 'blah'

# Test visibility
def test_visibility(workgroup_client):
    result = workgroup_client['test:1']
    assert result.visibility == WorkgroupVisibility.STANFORD

    # Test changing visibility works
    result.visibility = WorkgroupVisibility.PRIVATE
    assert result.visibility == WorkgroupVisibility.PRIVATE

    result.visibility = WorkgroupVisibility.STANFORD
    assert result.visibility == WorkgroupVisibility.STANFORD

    # Check an invalid visibility string
    with pytest.raises(ValueError):
        result.visibility = 'bsdf'
