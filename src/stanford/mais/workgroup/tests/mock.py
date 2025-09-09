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

# Define the classes that our test data will use

WorkgroupFilterLiteral = Literal[
    'NONE',
    'ACADEMIC_ADMINISTRATIVE',
    'STUDENT',
    'FACULTY',
    'STAFF',
    'FACULTY_STAFF',
    'FACULTY_STUDENT',
    'STAFF_STUDENT',
    'FACULTY_STAFF_STUDENT',
]

@dataclasses.dataclass(frozen=True)
class TestMember:
    type: Literal['PERSON', 'WORKGROUP', 'CERTIFICATE']
    id: str
    name: str

@dataclasses.dataclass(frozen=True)
class TestWorkgroup:
    name: str
    description: str
    filter: WorkgroupFilterLiteral
    visibility: Literal['STANFORD', 'PRIVATE']
    reusable: bool
    privgroup: bool
    # integrations is not implemented
    integrations: List[None]
    lastUpdate: str
    lastUpdateBy: str
    members: List['TestMember']
    administrators: List['TestMember']

# Make some test data!

person_akkornel = TestMember(
    type='PERSON',
    id='akkornel',
    name='Kornel, Karl'
)
person_leland = TestMember(
    type='PERSON',
    id='stanford',
    name='Stanford, Leland Jr.',
)

workgroup_test1 = TestWorkgroup(
    name='test:1',
    description='Test 1',
    filter='NONE',
    visibility='STANFORD',
    reusable=True,
    privgroup=True,
    integrations=list(),
    lastUpdate='1-Jan-2025',
    lastUpdateBy='pytest',
    members=[
        person_akkornel,
    ],
    administrators=[
        person_leland,
    ],
)

workgroup_test1_lite = (
    '{' +
    '"memberCount": "1",' +
    '"lastUpdate": "1-Jan-2025",' +
    '"name": "test:1",' +
    '"description": "Test 1",' +
    '"integrations": [],' +
    '"lastUpdateBy": "workgroup_maint"' +
    '}'
)


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

    # GET WORKGROUP

    # test:1 works
    responses.add(
        responses.GET,
        'http://example.com/wg/v2/test:1',
        status=200,
        content_type='application/json',
        json=dataclasses.asdict(workgroup_test1),
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
