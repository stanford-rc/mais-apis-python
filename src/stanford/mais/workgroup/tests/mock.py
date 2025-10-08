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
import json
from typing import Any, List, Literal

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

workgroup_test1_privgroup = """
{
"members": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "Kornel, Karl",
        "id": "akkornel"
    }
],
"name": "test:1",
"administrators": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "Stanford, Leland Jr.",
        "id": "stanford"
    }
]
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

workgroup_workgroupowners_json = """
{
"filter": "NONE",
"privgroup": "FALSE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "workgroup:workgroup-owners",
"description": "Workgroup stem for testing",
"integrations": [],
"administrators": [
],
"reusable": "FALSE",
"lastUpdateBy": "pytest"
}
"""

workgroup_workgroupowners_lite = """
{
"memberCount": "1",
"lastUpdate": "1-Jan-2025",
"name": "workgroup:workgroup-owners",
"description": "Workgroup stem for testing",
"integrations": [],
"lastUpdateBy": "pytest"
}
"""

# A rare workgroup that has no description
workgroup_test2_json = """
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
"name": "test:2",
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

# A private workgroup
workgroup_private1_json = """
{
"filter": "NONE",
"privgroup": "TRUE",
"visibility": "PRIVATE",
"lastUpdate": "1-Jan-2025",
"members": [
],
"name": "private:1",
"description": "Private Test 1",
"integrations": [],
"administrators": [
],
"reusable": "FALSE",
"lastUpdateBy": "pytest"
}
"""

# A workgroup with a type of member we've never seen before.
bad_unknowntype_json = """
{
"filter": "NONE",
"privgroup": "FALSE",
"visibility": "STANFORD",
"lastUpdate": "1-Jan-2025",
"members": [
    {
        "lastUpdate": "1-Jan-2025",
        "name": "Machine blargh",
        "id": "blargh",
        "type": "COMPUTER"
    }
],
"name": "bad:unknown-type",
"description": "Workgroup with an unknown type of member",
"integrations": [],
"administrators": [
],
"reusable": "FALSE",
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

    # SEARCH WORKGROUPS

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
        'http://example.com/wg/v2/search/workgroup:*',
        status=200,
        content_type='application/json',
        body=(
            '{' +
            '"search": "workgroup:*",' +
            '"results": [' +
            workgroup_testowners_lite + ',' +
            workgroup_workgroupowners_lite +
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
        'http://example.com/wg/v2/search/bad:w6',
        status=521,
        content_type='text/plain',
        body='What even is this?',
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
        'http://example.com/wg/v2?type=CERTIFICATE&id=bad521',
        status=521,
        content_type='text/plain',
        body='What even is this?',
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
    # In these cases, each test changes only one value of one field, based on
    # the "basic case" above.  So, we can set up a dict of field names, their
    # non-default values, and what JSON blob should be returned.
    create_workgroup_field_values: dict[str, dict[str, str]] = {
        'filter': {
            'ACADEMIC_ADMINISTRATIVE': workgroup_create_filter_academic_administrative_json,
            'STUDENT': workgroup_create_filter_student_json,
            'FACULTY': workgroup_create_filter_faculty_json,
            'STAFF': workgroup_create_filter_staff_json,
            'FACULTY_STAFF': workgroup_create_filter_faculty_staff_json,
            'FACULTY_STUDENT': workgroup_create_filter_faculty_student_json,
            'STAFF_STUDENT': workgroup_create_filter_staff_student_json,
            'FACULTY_STAFF_STUDENT': workgroup_create_filter_faculty_staff_student_json,
        },
        'privgroup': {
            'FALSE': workgroup_create_privgroup_json,
        },
        'reusable': {
            'FALSE': workgroup_create_reusable_json,
        },
        'visibility': {
            'PRIVATE': workgroup_create_visibility_json,
        },
        
    }
    for (field_name, value_response) in create_workgroup_field_values.items():
        for (value, response) in value_response.items():
            initial_fields = {
                'description': 'Create Test 1',
                'filter': 'NONE',
                'privgroup': 'TRUE',
                'reusable': 'TRUE',
                'visibility': 'STANFORD',
            }
            initial_fields[field_name] = value
            responses.add(
                responses.POST,
                'http://example.com/wg/v2/create:1',
                match=[
                    matchers.json_params_matcher(
                        initial_fields,
                        strict_match=True,
                    )
                ],
                status=201,
                content_type='application/json',
                body=response,
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

    # Upstream failures
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:bad400',
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
        responses.POST,
        'http://example.com/wg/v2/create:bad401',
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
        responses.POST,
        'http://example.com/wg/v2/create:bad521',
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
        status=521,
        content_type='text/plain',
        body='What even is this?',
    )
    responses.add(
        responses.POST,
        'http://example.com/wg/v2/create:inactive',
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
        status=400,
        content_type='application/json',
        json={
            'notification': 'Workgroup is inactive',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    # GET WORKGROUP

    # These are workgroups that we support fetching.
    for (url, json_body) in {
        'http://example.com/wg/v2/workgroup:test-owners': workgroup_testowners_json,
        'http://example.com/wg/v2/workgroup:workgroup-owners': workgroup_workgroupowners_json,
        'http://example.com/wg/v2/private:1': workgroup_private1_json,
        'http://example.com/wg/v2/test:1': workgroup_test1_json,
        'http://example.com/wg/v2/test:2': workgroup_test2_json,
        'http://example.com/wg/v2/bad:unknown-type': bad_unknowntype_json,
    }.items():
        responses.add(
            responses.GET,
            url,
            status=200,
            content_type='application/json',
            body=json_body,
        )

    # To simulate upstream errors on workgroup GET and privgroup GET, we have a
    # number of workgroups in the `bad:` stem that will always return a
    # particular response code.
    get_urls_responses: dict[str, tuple[int, str, str]] = {
        'http://example.com/wg/v2/bad:w1': (
            400,
            'Error code 400',
            'Bad request'
        ),
        'http://example.com/wg/v2/bad:w3': (
            401,
            'Error code 401',
            'Unauthorized'
        ),
        'http://example.com/wg/v2/bad:w4': (
            403,
            'Error code 403',
            'Forbidden'
        ),
        'http://example.com/wg/v2/bad:w5': (
            404,
            'Not found',
            'Not found'
        ),
        'http://example.com/wg/v2/bad:w2': (
            500,
            'Internal Server Error',
            'Internal Server Error'
        )
    }
    for (get_url, get_response) in get_urls_responses.items():
        (code, notification, message) = get_response
        responses.add(
            responses.GET,
            get_url,
            status=code,
            content_type='application/json',
            json={
                'notification': notification,
                'code': code,
                'message': message,
                'status': code,
            },
        )
        responses.add(
            responses.GET,
            get_url + '/privgroup',
            status=code,
            content_type='application/json',
            json={
                'notification': notification,
                'code': code,
                'message': message,
                'status': code,
            },
        )

    # The bad:w6 workgroup is special
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w6',
        status=521,
        content_type='text/plain',
        body='What even is this?',
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

    # test:deleted is a workgroup which has been deleted
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/test:inactive',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Workgroup is inactive',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    # UPDATE WORKGROUP

    # NOTE: Updating workgroup properties involves sending a complete workgroup
    # JSON in the response.  Rather than make a ton of new JSON structures, we
    # define a function that takes workgroup_test1_json, modifies one of its
    # properties, and returns a new JSON string.
    def change_prop(
        name: Literal[
            'description',
            'filter',
            'privgroup',
            'reusable',
            'visibility',
        ],
        value: str,
    ) -> Any:
        """Change a property of workgroup_test1_json

        This parses workgroup_test1_json, changes one of the properties, and
        returns a new serialized JSON blob.

        :param key: The property key to change

        :param value: The new value

        :returns: A new, serialized JSON blob, with the property modified.
        """
        decoded_json = json.loads(workgroup_test1_json)
        decoded_json[name] = value
        return json.dumps(decoded_json)

    # Make a dict of all our properties, and their possible values
    properties_possible_values: dict[Literal['description', 'filter', 'privgroup', 'reusable', 'visibility'], tuple[str, ...]] = {
        # description is a free-form field; let's add one max-length value with
        # a Latin1 character.
        'description': (
            ('x' * 254) + '¿',
        ),
        'filter': (
            'NONE',
            'ACADEMIC_ADMINISTRATIVE',
            'STUDENT',
            'FACULTY',
            'STAFF',
            'FACULTY_STAFF',
            'FACULTY_STUDENT',
            'STAFF_STUDENT',
            'FACULTY_STAFF_STUDENT',
        ),
        'privgroup': (
            'TRUE',
            'FALSE',
        ),
        'reusable': (
            'TRUE',
            'FALSE',
        ),
        'visibility': (
            'PRIVATE',
            'STANFORD',
        ),
    }
    for (prop_name, prop_values) in properties_possible_values.items():
        for prop_value in prop_values:
            responses.add(
                responses.PUT,
                'http://example.com/wg/v2/test:1',
                match=[
                    matchers.json_params_matcher(
                        {
                            prop_name: prop_value,
                        },
                        strict_match=True,
                    )
                ],
                status=200,
                content_type='application/json',
                body=change_prop(prop_name, prop_value),
            )

    # Changing test:1 description to 'deleted' gives a special 400
    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': 'delete',
                },
                strict_match=True,
            )
        ],
        status=400,
        content_type='application/json',
        json={
            'notification': 'Workgroup is inactive',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    # Changing test:1 description to various special values gives upstream
    # error response codes.

    update_workgroup_description_responses: dict[str, tuple[int, str, str]] = {
        'bad1': (
            400,
            'Error code 400',
            'Bad Request'
        ),
        'bad3': (
            401,
            'Error code 401',
            'Unauthorized'
        ),
        'bad4': (
            403,
            'Error code 403',
            'Bad request'
        ),
        'bad2': (
            500,
            'Internal Server Error',
            'Internal Server Error'
        )
    }
    for (new_description, description_response) in update_workgroup_description_responses.items():
        (code, notification, message) = description_response
        responses.add(
            responses.PUT,
            'http://example.com/wg/v2/test:1',
            match=[
                matchers.json_params_matcher(
                    {
                        'description': new_description,
                    },
                    strict_match=True,
                )
            ],
            status=code,
            content_type='application/json',
            json={
                'notification': notification,
                'code': code,
                'message': message,
                'status': code,
            },
        )

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1',
        match=[
            matchers.json_params_matcher(
                {
                    'description': '521',
                },
                strict_match=True,
            )
        ],
        status=521,
        content_type='text/plain',
        body='What even is this?',
    )

    # DELETE WORKGROUP

    # Delete test:1
    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/test:1',
        status=200,
        content_type='application/json',
        json={
            'notification': 'Workgroup: test:1 has been deleted and all members and administrators removed',
            'code': 200,
            'message': 'Deleted',
            'status': 200,
        }
    )

    # Deleting workgroup:test-owners returns a 400
    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/workgroup:test-owners',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Error code 400',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    # Deleting private:1 returns a 401
    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/private:1',
        status=401,
        content_type='application/json',
        json={
            'notification': 'Error code 401',
            'code': 401,
            'message': 'Unauthorized',
            'status': 401,
        },
    )

    # Deleting bad:521 returns a 521
    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/bad:521',
        status=521,
        content_type='text/plain',
        body='What even is this?',
    )
    

    # test:deleted is a workgroup which has been deleted
    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/test:inactive',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Workgroup is inactive',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    # GET PRIVILEGE GROUP (PRIVGROUP)

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/test:1/privgroup',
        status=200,
        content_type='application/json',
        body=workgroup_test1_privgroup,
    )

    # A number of special workgroup names return upstream errors

    # NOTE: privgroup responses for bad:XX workgroups, other than bad:w6, are
    # being generated in the GET WORKGROUP section.

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/test:inactive/privgroup',
        status=400,
        content_type='application/json',
        json={
            'notification': 'Workgroup is inactive',
            'code': 400,
            'message': 'Bad Request',
            'status': 400,
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/wg/v2/bad:w6/privgroup',
        status=521,
        content_type='text/plain',
        body='What even is this?',
    )

    # ADD MEMBER and REMOVE MEMBER

    # Some good add-member operations

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/members/adamhl',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'adamhl was added as a member to the workgroup: test:1',
            'code': 200,
            'message': 'Added',
            'status': 200,
        },
    )

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/members/cert5225',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'CERTIFICATE',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'cert5225 was added as a member to the workgroup: test:1',
            'code': 200,
            'message': 'Added',
            'status': 200,
        },
    )

    # Some good remove-member operations

    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/test:1/members/akkornel',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'akkornel was removed as a member from the workgroup: test:1',
            'code': 200,
            'message': 'Removed',
            'status': 200,
        },
    )

    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/workgroup:test-owners/members/client-cert-1',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'CERTIFICATE',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'client-cert-1 was removed as a member from the workgroup: workgroup:test-owners',
            'code': 200,
            'message': 'Removed',
            'status': 200,
        },
    )

    # Add our common API errors

    add_remove_member_responses: dict[str, tuple[int, str, str]] = {
        'inactive': (
            400,
            'Workgroup is inactive',
            'Bad Request'
        ),
        'bad400': (
            400,
            'Error code 400',
            'Bad request'
        ),
        'bad401': (
            401,
            'Error code 401',
            'Unauthorized'
        ),
        'bad500': (
            500,
            'Internal Server Error',
            'Internal Server Error'
        )
    }
    for (member_name, add_remove_response) in add_remove_member_responses.items():
        (code, notification, message) = add_remove_response
        responses.add(
            responses.PUT,
            'http://example.com/wg/v2/test:1/members/' + member_name,
            match=[
                matchers.json_params_matcher(
                    {
                        'type': 'USER',
                    },
                    strict_match=True,
                )
            ],
            status=code,
            content_type='application/json',
            json={
                'notification': notification,
                'code': code,
                'message': message,
                'status': code,
            },
        )
        responses.add(
            responses.DELETE,
            'http://example.com/wg/v2/test:1/members/' + member_name,
            status=code,
            content_type='application/json',
            json={
                'notification': notification,
                'code': code,
                'message': message,
                'status': code,
            },
        )

    # And our special 521 errors

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/members/bad521',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=521,
        content_type='text/plain',
        body='What even is this?',
    )

    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/test:1/members/bad521',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=521,
        content_type='text/plain',
        body='What even is this?',
    )

    # Finally, a couple of add-member errors unique to add-member

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/members/nobody',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=404,
        content_type='application/json',
        json={
            "notification": "Not Found",
            "code": 404,
            "message": "nobody was not found",
            "status": 404
        },
    )

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/members/leland',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=409,
        content_type='application/json',
        json={
            "notification": "Conflict",
            "code": 409,
            "message": "Member leland of type USER already exist in workgroup: test:1",
            "status": 409
        },
    )

    # ADD ADMINISTRATOR

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/administrators/adamhl',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'adamhl was added as a administrator to the workgroup: test:1',
            'code': 200,
            'message': 'Added',
            'status': 200,
        },
    )

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/create:1/administrators/workgroup:test-owners',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'WORKGROUP',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            "notification": "Conflict",
            "code": 200,
            "message": "workgroup:test-owners was added as a administrator to the workgroup: create:1",
            "status": 200
        },
    )

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/administrators/cert5225',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'CERTIFICATE',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'cert5225 was added as a administrator to the workgroup: test:1',
            'code': 200,
            'message': 'Added',
            'status': 200,
        },
    )

    # Add a couple of 409 Conflict responses

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/administrators/stanford',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=409,
        content_type='application/json',
        json={
            "notification": "Conflict",
            "code": 409,
            "message": "Administrator stanford of type USER already exist in workgroup: test:1",
            "status": 409
        },
    )

    responses.add(
        responses.PUT,
        'http://example.com/wg/v2/test:1/administrators/workgroup:test-owners',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'WORKGROUP',
                },
                strict_match=True,
            )
        ],
        status=409,
        content_type='application/json',
        json={
            "notification": "Conflict",
            "code": 409,
            "message": "Administrator workgroup:test-owners of type WORKGROUP already exist in workgroup: test:1",
            "status": 409
        },

    )

    # REMOVE ADMINISTRATOR

    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/test:1/administrators/stanford',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'USER',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'stanford was removed as a administrator from the workgroup: test:1',
            'code': 200,
            'message': 'Removed',
            'status': 200,
        },
    )

    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/workgroup:test-owners/administrators/workgroup:workgroup-owners',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'WORKGROUP',
                },
                strict_match=True,
            )
        ],
        status=200,
        content_type='application/json',
        json={
            'notification': 'workgroup:workgroup-owners was removed as a administrator from the workgroup: workgroup:test-owners',
            'code': 200,
            'message': 'Removed',
            'status': 200,
        },
    )

    # Add a case of an admin being removed without us realizing

    responses.add(
        responses.DELETE,
        'http://example.com/wg/v2/test:1/administrators/workgroup:test-owners',
        match=[
            matchers.json_params_matcher(
                {
                    'type': 'WORKGROUP',
                },
                strict_match=True,
            )
        ],
        status=404,
        content_type='application/json',
        json={
            'notification': 'workgroup:test-owners is not a administrator of workgroup: test:1',
            'code': 404,
            'message': 'Not Found',
            'status': 404,
        },
    )

    # GET INTEGRATION

    # TODO

    # All done!
    return None
