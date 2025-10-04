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
from stanford.mais.workgroup import Workgroup, WorkgroupClient, WorkgroupDeleted, WorkgroupFilter, WorkgroupVisibility

"""
This file tests workgroup creation, the different properties that can be set at
that time, and all the exceptions which might be thrown.
"""

# Test the most simple form of workgroup creation, with everything set to
# default values.
def test_workgroup_create_simple(workgroup_client):
    result = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
    )
    assert result.name == 'create:1'
    assert result.description == 'Create Test 1'
    assert result.filter == WorkgroupFilter.NONE
    assert result.privgroup is True
    assert result.reusable is True
    assert result.visibility == WorkgroupVisibility.STANFORD

# Test creating with different filters
def test_workgroup_create_filters(workgroup_client):
    for filter_value in (
        WorkgroupFilter.NONE,
        WorkgroupFilter.ACADEMIC_ADMINISTRATIVE,
        WorkgroupFilter.STUDENT,
        WorkgroupFilter.FACULTY,
        WorkgroupFilter.STAFF,
        WorkgroupFilter.FACULTY_STAFF,
        WorkgroupFilter.FACULTY_STUDENT,
        WorkgroupFilter.STAFF_STUDENT,
        WorkgroupFilter.FACULTY_STAFF_STUDENT,
    ):
        result = workgroup_client.create(
            name='create:1',
            description='Create Test 1',
            filter=filter_value,
        )
        assert result.name == 'create:1'
        assert result.description == 'Create Test 1'
        assert result.filter == filter_value
        assert result.privgroup is True
        assert result.reusable is True
        assert result.visibility == WorkgroupVisibility.STANFORD

# Test creating with privgroup off
def test_workgroup_create_privgroup(workgroup_client):
    result = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
        privgroup=False,
    )
    assert result.name == 'create:1'
    assert result.description == 'Create Test 1'
    assert result.filter == WorkgroupFilter.NONE
    assert result.privgroup is False
    assert result.reusable is True
    assert result.visibility == WorkgroupVisibility.STANFORD

# Test creating with reusable off
def test_workgroup_create_reusable(workgroup_client):
    result = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
        reusable=False,
    )
    assert result.name == 'create:1'
    assert result.description == 'Create Test 1'
    assert result.filter == WorkgroupFilter.NONE
    assert result.privgroup is True
    assert result.reusable is False
    assert result.visibility == WorkgroupVisibility.STANFORD

# Test creating with visibility private
def test_workgroup_create_visibility(workgroup_client):
    result = workgroup_client.create(
        name='create:1',
        description='Create Test 1',
        visibility=WorkgroupVisibility.PRIVATE
    )
    assert result.name == 'create:1'
    assert result.description == 'Create Test 1'
    assert result.filter == WorkgroupFilter.NONE
    assert result.privgroup is True
    assert result.reusable is True
    assert result.visibility == WorkgroupVisibility.PRIVATE

# Test checking of name issues (including duplicate workgroup)
def test_workgroup_create_name(workgroup_client):
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='create:',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name=':1',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='créate:1',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='create:üno',
            description='Create Test 1',
        )
    with pytest.raises(IndexError):
        workgroup_client.create(
            name='create:111111111111111111111111111111111111111111111111111111111111111111111111111',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='-create:1',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='_create:1',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='create:_1',
            description='Create Test 1',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='create:-1',
            description='create test 1',
        )
    with pytest.raises(KeyError):
        workgroup_client.create(
            name='create:dupe',
            description='Create Test 1',
        )

# Test checking of description issues
def test_workgroup_create_description(workgroup_client):
    with pytest.raises(IndexError):
        workgroup_client.create(
            name='create:1',
            description='',
        )
    with pytest.raises(IndexError):
        workgroup_client.create(
            name='create:1',
            description='1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='create:1',
            description='Euro symbol € is not in Latin1!',
        )
    with pytest.raises(ValueError):
        workgroup_client.create(
            name='create:1',
            description='Bell symbol \007 is not printable!',
        )

# Test upstream misc. failures that could happen during Workgroup creation
def test_workgroup_create_fail(workgroup_client):
    with pytest.raises(ChildProcessError):
        workgroup_client.create(
            name='create:bad400',
            description='Create Test 1',
        )
    with pytest.raises(PermissionError):
        workgroup_client.create(
            name='create:bad401',
            description='Create Test 1',
        )
    with pytest.raises(NotImplementedError):
        workgroup_client.create(
            name='create:bad521',
            description='Create Test 1',
        )
    with pytest.raises(WorkgroupDeleted):
        workgroup_client.create(
            name='create:inactive',
            description='Create Test 1',
        )
