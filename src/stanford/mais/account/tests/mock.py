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
from typing import Any, List, Literal, Optional, TypedDict, Union

# PyPi imports
import responses

# Local imports
from stanford.mais.workgroup.properties import WorkgroupFilterLiteral

# Define the classes that our test data will use

class ServiceSetting(TypedDict):
    name: str
    value: Union[str, int]
class ServiceJson(TypedDict):
    name: str
    status: Literal['active', 'inactive', 'frozen']
    settings: list[ServiceSetting]

@dataclasses.dataclass(frozen=True)
class TestService:
    status: Literal['active', 'inactive', 'frozen']

    def as_dict(self) -> ServiceJson:
        # First, we need our service's name
        # This comes from the class name, minus the "Test", and lowercased.
        service_name = type(self).__name__.split('Test')[1].lower()

        # Now, let's get all of the service's keys, but remove 'status'
        # (Status is not a setting)
        all_keys = dataclasses.asdict(self)
        del all_keys['status']

        # This is what we'll return as settings
        settings_list: list[ServiceSetting] = list()

        # Everything left in all_keys is a setting.
        # We need to provide a list of name/value dicts
        for setting_key in all_keys:
            # Settings can be single- or multi-valued.
            if isinstance(all_keys[setting_key], list):
                # Our key is a multi-valued key.
                # We need to add our setting name multiple times.
                for setting_value in all_keys[setting_key]:
                    settings_list.append(ServiceSetting(
                        name=setting_key,
                        value=setting_value,
                    ))
            # Settings without a value are not included in the JSON.
            elif all_keys[setting_key] is not None:
                # Our key is a single-valued key.  Easy!
                settings_list.append(ServiceSetting(
                    name=setting_key,
                    value=all_keys[setting_key],
                ))

        # Return a dict, ready to be merged into a list of dicts!
        return ServiceJson(
            name=service_name,
            status=self.status,
            settings=settings_list,
        )

@dataclasses.dataclass(frozen=True)
class TestKerberos(TestService):
    principal: str
    uid: int

@dataclasses.dataclass(frozen=True)
class TestLibrary(TestService):
    pass

@dataclasses.dataclass(frozen=True)
class TestSEAS(TestService):
    sunetid: List[str]
    sunetidpreferred: str
    local: Optional[str] = None
    forward: Optional[List[str]] = None
    urirouteto: Optional[str] = None

@dataclasses.dataclass(frozen=True)
class TestEmail(TestService):
    accounttype: Literal['personal', 'functional']
    quota: Optional[int] = None
    admin: Optional[str] = None

@dataclasses.dataclass(frozen=True)
class TestAutoreply(TestService):
    forward: str
    subj: str
    msg: str

@dataclasses.dataclass(frozen=True)
class TestLeland(TestService):
    shell: Optional[str]

@dataclasses.dataclass(frozen=True)
class TestPTS(TestService):
    uid: int

@dataclasses.dataclass(frozen=True)
class TestAFS(TestService):
    homedirectory: str

@dataclasses.dataclass(frozen=True)
class TestDialin(TestService):
    pass

@dataclasses.dataclass(frozen=True)
class TestAccount:
    id: str
    name: str
    description: str
    status: Literal['active', 'inactive', 'frozen']
    statusDateStr: str
    type: Literal['self', 'functional']
    services: List[TestService]

    def as_json(self) -> dict[str, Any]:
        services_list = list(
            (service.as_dict() for service in self.services)
        )
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'statusDateStr': self.statusDateStr,
            'type': self.type,
            'services': services_list,
        }


# Make some test data!

account_fullprsn = TestAccount(
    id='fullprsn',
    name='Full Person',
    description='Staff - University IT',
    type='self',
    status='active',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
        TestKerberos(
            status='active',
            principal='fullprsn',
            uid=12345,
        ),
        TestLibrary(
            status='active',
        ),
        TestSEAS(
            status='active',
            local="fullprsn@onmicrosoft.example.com",
            sunetid=['fullprsn'],
            sunetidpreferred='fullprsn',
        ),
        TestEmail(
            status='active',
            accounttype='personal',
        ),
        TestLeland(
            status='active',
            shell=None,
        ),
        TestPTS(
            status='active',
            uid=12345,
        ),
        TestAFS(
            status='active',
            homedirectory='/afs/te/users/f/u/fullprsn',
        ),
    ],
)

account_frozprsn = TestAccount(
    id='frozprsn',
    name='Frozen Person',
    description='Staff - University IT',
    type='self',
    status='active',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
        TestKerberos(
            status='frozen',
            principal='frozprsn',
            uid=12346,
        ),
        TestLibrary(
            status='active',
        ),
        TestSEAS(
            status='active',
            local='frozprsn@onmicrosoft.example.com',
            sunetid=['frozprsn', 'frozen.person'],
            sunetidpreferred='frozen.person',
            forward=['fperson@outside.com'],
            urirouteto='http://geocities.com/neworleans/12/11/',
        ),
        TestEmail(
            status='active',
            accounttype='personal',
        ),
        TestAutoreply(
            status='active',
            forward='frozprsn@forward.example.com',
            subj='Out of office',
            msg=r'I am currently out of the office.\r\nI will respond when I return.',
        ),
        TestLeland(
            status='active',
            shell='/bin/bash',
        ),
        TestPTS(
            status='active',
            uid=12346,
        ),
        TestAFS(
            status='active',
            homedirectory='/afs/te/users/f/r/frozprsn',
        ),
    ],
)

account_formerpsn = TestAccount(
    id='formerpsn',
    name='Former Person',
    description='Former Staff - University IT',
    type='self',
    status='inactive',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
    ],
)

account_affilite = TestAccount(
    id='affilite',
    name='Affiliate Smith',
    description='Affiliate - Genetics',
    type='self',
    status='active',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
        TestKerberos(
            status='active',
            principal='affilite',
            uid=12344,
        ),
        TestSEAS(
            status='active',
            local='affilite@zm88.example.com',
            sunetid=['affilite'],
            sunetidpreferred='affilite',
        ),
        TestEmail(
            status='active',
            accounttype='personal',
        ),
        TestLeland(
            status='active',
            shell='/bin/bash',
        ),
        TestPTS(
            status='active',
            uid=12344,
        ),
        TestAFS(
            status='active',
            homedirectory='/afs/te/users/a/f/affilite',
        ),
    ],
)

account_afilbase = TestAccount(
    id='afilbase',
    name='Base Affiliate Jones',
    description='Affiliate - Anesthesia',
    type='self',
    status='active',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
        TestKerberos(
            status='active',
            principal='afilbase',
            uid=12333,
        )
    ],
)

account_functional = TestAccount(
    id='functional',
    name='Functional Account',
    description='Functional Account',
    type='functional',
    status='active',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
        TestKerberos(
            status='active',
            principal='functional',
            uid=12332,
        ),
        TestPTS(
            status='active',
            uid=12332,
        ),
    ],
)

account_oldfunctional = TestAccount(
    id='oldfunctional',
    name='Old Functional Account',
    description='Functional Account',
    type='functional',
    status='inactive',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
    ],
)

account_sharedmailbox = TestAccount(
    id='sharedmailbox',
    name='Some Group Mailbox',
    description='Shared Email Account',
    type='functional',
    status='active',
    statusDateStr='2020-01-03T15:14:13.00Z',
    services=[
        TestSEAS(
            status='active',
            sunetid=['sharedmailbox'],
            sunetidpreferred='sharedmailbox',
            forward=['sharedmailbox@onmicrosoft.example.com'],
        ),
        TestAutoreply(
            status='active',
            forward='sharedmailbox@forward.example.com',
            subj='Request received: $SUBJECT',
            msg=r'Thank you for emailing us!\r\nYour email "$SUBJECT" will be responded to during business hours.\r\nThank you.',
        ),
    ],
)

# Add Accounts responses to the Responses mock session
def add_account_responses() -> None:
    # GET ACCOUNTS

    # Valid accounts

    responses.add(
        responses.GET,
        'http://example.com/accounts/fullprsn',
        status=200,
        content_type='application/json',
        json=account_fullprsn.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/frozprsn',
        status=200,
        content_type='application/json',
        json=account_frozprsn.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/formerpsn',
        status=200,
        content_type='application/json',
        json=account_formerpsn.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/affilite',
        status=200,
        content_type='application/json',
        json=account_affilite.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/afilbase',
        status=200,
        content_type='application/json',
        json=account_afilbase.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/functional',
        status=200,
        content_type='application/json',
        json=account_functional.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/oldfunctional',
        status=200,
        content_type='application/json',
        json=account_oldfunctional.as_json(),
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/sharedmailbox',
        status=200,
        content_type='application/json',
        json=account_sharedmailbox.as_json(),
    )

    # Simulate error conditions

    responses.add(
        responses.GET,
        'http://example.com/accounts/nobody',
        status=404,
        content_type='application/json',
        json={
            'status': 404,
            'message': 'Account "nobody" does not exist',
            'url': 'http://example.com/accounts/nobody'
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/hidden1',
        status=401,
        content_type='application/json',
        json={
            'status': 401,
            'message': 'Unauthorized',
            'url': 'http://example.com/accounts/hidden1'
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/hidden3',
        status=403,
        content_type='application/json',
        json={
            'status': 403,
            'message': 'Forbidden',
            'url': 'http://example.com/accounts/hidden3'
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/broken4',
        status=400,
        content_type='application/json',
        json={
            'status': 400,
            'message': 'Unauthorized',
            'url': 'http://example.com/accounts/broken4'
        },
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/broken5',
        status=500,
        content_type='application/json',
        json={
            'status': 500,
            'message': 'Internal server error',
            'url': 'http://example.com/accounts/broken5'
        },
    )

    # All done!
    return None
