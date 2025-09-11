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

# Stdlib imports
import dataclasses
from typing import List, Literal

# PyPi imports
import responses
from responses import matchers

# Provide some raw workgroups, in full and lite form
workgroup_test1_json = """
{
"filter": "NONE",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "Kornel, Karl",
        "id": "akkornel",
        "type": "PERSON"
    }
],
"name": "test:1",
"description": "Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "Stanford, Leland Jr.",
        "id": "stanford",
        "type": "PERSON"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:test-owners",
        "id": "workgroup:test-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""

workgroup_test1_lite = """
{
"memberCount": "1",
"lastUpdate": "1-Jan-2025",
"name": "test:1",
"description": "Test 1",
"integrations": [],
"lastUpdateBy": "workgroup_maint"
}
"""

workgroup_testowners_json = """
{
"filter": "ACADEMIC_ADMINISTRATIVE",
"privgroup": "FALSE",
"visibility": "PRIVATE",
"lastUpdate": "1-Jan-2025",
"members": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    }
],
"name": "workgroup:test-owners",
"description": "Workgroup stem for testing",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:workgroup-owners",
        "id": "workgroup:workgroup-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "FALSE",
"lastUpdateBy": "pytest"
}
"""

workgroup_testowners_lite = """
{
"memberCount": "1",
"lastUpdate": "1-Jan-2025",
"name": "workgroup:test-owners",
"description": "Workgroup stem for testing",
"integrations": [],
"lastUpdateBy": "pytest"
}
"""

# The `create:` stem is used to test workgroup creation and property change.
# The create:1 workgroup is our starting point, as if we created a workgroup
# with nothing (other than name & description) specified.

workgroup_create1_json = """
{
"filter": "NONE",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""

# These 'create' workgroups change different filters
workgroup_create_filter_academic_administrative_json = """
{
"filter": "ACADEMIC_ADMINISTRATIVE",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_student_json = """
{
"filter": "STUDENT",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_faculty_json = """
{
"filter": "FACULTY",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_staff_json = """
{
"filter": "STAFF",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_faculty_staff_json = """
{
"filter": "FACULTY_STAFF",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_faculty_student_json = """
{
"filter": "FACULTY_STUDENT",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_staff_student_json = """
{
"filter": "STAFF_STUDENT",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_filter_faculty_staff_student_json = """
{
"filter": "FACULTY_STAFF_STUDENT",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""

# These 'create' workgroups change privgroup, reusable, or visibility
workgroup_create_privgroup_json = """
{
"filter": "NONE",
"privgroup": "FALSE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_reusable_json = """
{
"filter": "NONE",
"privgroup": "TRUE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "FALSE",
"lastUpdateBy": "pytest"
}
"""
workgroup_create_visibility_json = """
{
"filter": "NONE",
"privgroup": "TRUE",
"visibility": "PRIVATE",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "create:1",
"description": "Create Test 1",
"integrations": [],
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "client-cert-1",
        "id": "client-cert-1",
        "type": "CERTIFICATE"
    },
    {
        "lastUpdate": "1-Jan-2025",
        "name": "workgroup:create-owners",
        "id": "workgroup:create-owners",
        "type": "WORKGROUP"
    }
],
"reusable": "TRUE",
"lastUpdateBy": "pytest"
}
"""


# Add Workgroup responses to the Responses mock session
def add_workgroup_responses() -> None:
    # The bad: stem is used for triggering error statuses
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w1',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Error code 400',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w2',
        status=500,
        content_type='application/json',
        json={
            'notification': 'Internal Server Error',
            'code': 500,
            'message': 'Internal Server Error',
            'status': 500,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w3',
        status=401,
        content_type='application/json',
        json={
            'notification': 'Error code 401',
            'code': 401,
            'message': 'Unauthorized',
            'status': 401,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w4',
        status=403,
        content_type='application/json',
        json={
            'notification': 'Error code 403',
            'code': 403,
            'message': 'Forbidden',
            'status': 403,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w5',
        status=404,
        content_type='application/json',
        json={
            'notification': 'Not found',
            'code': 404,
            'message': 'Not found',
            'status': 404,
        },
    )

    # Add some search results
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/search/noresults:*',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"search": "noresults:*",' +
            '"results": []' +
            '}'
        )
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/search/test:*',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"search": "research-computing:*",' +
            '"results": [' +
            workgroup_test1_lite +
            ']' +
            '}'
        )
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/search/bad:w1',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Error code 400',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/search/bad:w3',
        status=401,
        content_type='application/json',
        json={
            'notification': 'Error code 401',
            'code': 401,
            'message': 'Unauthorized',
            'status': 401,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2?type=WORKGROUP&id=workgroup:test-owners',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"administrators_count": 1,' +
            '"members": [' +
            '],' +
            '"members_count": 0,' +
            '"id": "workgroup:test-owners",' +
            '"type": "workgroup",' +
            '"results": [' +
            workgroup_test1_lite +
            '],' +
            '"administrators": [' +
            workgroup_test1_lite +
            ']' +
            '}'
        )
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2?type=CERTIFICATE&id=client-cert-1',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"administrators_count": 1,' +
            '"members": [' +
            '],' +
            '"members_count": 1,' +
            '"id": "client-cert-1",' +
            '"type": "certificate",' +
            '"results": [' +
            workgroup_testowners_lite +
            '],' +
            '"administrators": [' +
            workgroup_testowners_lite +
            ']' +
            '}'
        )
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2?type=CERTIFICATE&id=nonexistant',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"administrators_count": 0,' +
            '"members": [' +
            '],' +
            '"members_count": 0,' +
            '"id": "nonexistant",' +
            '"type": "certificate",' +
            '"results": [' +
            '],' +
            '"administrators": [' +
            ']' +
            '}'
        )
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2?type=CERTIFICATE&id=bad400',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Error code 400',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2?type=CERTIFICATE&id=bad401',
        status=401,
        content_type='application/json',
        json={
            'notification': 'Error code 401',
            'code': 401,
            'message': 'Unauthorized',
            'status': 401,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2?type=USER&id=akkornel',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"administrators_count": 0,' +
            '"members": [' +
            workgroup_test1_lite +
            '],' +
            '"members_count": 1,' +
            '"id": "akkornel",' +
            '"type": "user",' +
            '"results": [' +
            workgroup_test1_lite +
            '],' +
            '"administrators": [' +
            ']' +
            '}'
        )

    )

    # CREATE WORKGROUP

    # Basic case
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'NONE',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create1_json,
    )

    # Basic case, but with different filters
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'ACADEMIC_ADMINISTRATIVE',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_academic_administrative_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'STUDENT',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_student_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'FACULTY',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_faculty_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'STAFF',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_staff_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'FACULTY_STAFF',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_faculty_staff_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'FACULTY_STUDENT',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_faculty_student_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'STAFF_STUDENT',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_staff_student_json,
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'FACULTY_STAFF_STUDENT',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_filter_faculty_staff_student_json,
    )

    # Basic case, but with privgroup off
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'NONE',
                    'privgroup': 'FALSE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_privgroup_json,
    )

    # Basic case, but with reusable off
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'NONE',
                    'privgroup': 'TRUE',
                    'reusable': 'FALSE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_reusable_json,
    )

    # Basic case, but with visibility private
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'NONE',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'PRIVATE',
                },
                strict_match=True,
            )
        ],
        status=201,
        content_type='application/json',
        body=workgroup_create_visibility_json,
    )

    # Duplicate workgroup
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:dupe',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'Create Test 1',
                    'filter': 'NONE',
                    'privgroup': 'TRUE',
                    'reusable': 'TRUE',
                    'visibility': 'STANFORD',
                },
                strict_match=True,
            )
        ],
        status=409,
        content_type='application/json',
        json={
            'notification': 'create:dupe workgroup already exist.',
            'code': 409,
            'message': 'Conflict',
            'status': 409,
        },
    )

    # GET WORKGROUP

    # test:1 works
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/workgroup:test-owners',
        status=200,
        content_type='application/json',
        body=workgroup_testowners_json,
    )

    # test:1 works
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/test:1',
        status=200,
        content_type='application/json',
        body=workgroup_test1_json,
    )

    # test:missing is a 404
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/test:missing',
        status=404,
        content_type='application/json',
        json={
            'code': 404,
            'message': 'Workgroup test:missing does not exist',
        },
    )


    # UPDATE WORKGROUP


    # DELETE WORKGROUP


    # GET PRIVILEGE GROUP


    # ADD MEMBER


    # REMOVE MEMBER


    # ADD ADMINISTRATOR


    # REMOVE ADMINISTRATOR


    # GET INTEGRATION

    # TODO

    # All done!
    return None
