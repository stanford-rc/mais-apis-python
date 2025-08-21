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
from typing import Any, List, Literal, TypedDict

# PyPi imports
import responses

# Make some test data!

json_fullprsn = '''
{
  "services": [
    {
      "settings": [],
      "name": "library",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "local",
          "value": "fullprsn@onmicrosoft.example.com"
        },
        {
          "name": "sunetidpreferred",
          "value": "fullprsn"
        },
        {
          "name": "sunetid",
          "value": "fullprsn"
        }
      ],
      "name": "seas",
      "status": "active"
    },
    {
      "settings": [],
      "name": "dialin",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "principal",
          "value": "fullprsn"
        },
        {
          "name": "uid",
          "value": "12345"
        }
      ],
      "name": "kerberos",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "accounttype",
          "value": "personal"
        },
        {
          "name": "quota",
          "value": "1000"
        },
        {
          "name": "admin",
          "value": "fullprsn"
        }
      ],
      "name": "email",
      "status": "active"
    },
    {
      "settings": [],
      "name": "leland",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "homedirectory",
          "value": "/afs/te/users/f/u/fullprsn"
        }
      ],
      "name": "afs",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "uid",
          "value": "12345"
        }
      ],
      "name": "pts",
      "status": "active"
    }
  ],
  "owner": "person/24ba8de0d6eaf3188a7d3c228f1324b23",
  "type": "self",
  "name": "Person, Full",
  "id": "fullprsn",
  "description": "Staff - University IT",
  "status": "active",
  "url": "http://example.com/accounts/fullprsn",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_frozprsn = '''
{
  "services": [
    {
      "settings": [],
      "name": "library",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "subj",
          "value": "Out of office"
        },
        {
          "name": "msg",
          "value": "I am currently out of the office.\\\\r\\\\nI will respond when I return."
        },
        {
          "name": "forward",
          "value": "frozprsn@forward.example.com"
        }
      ],
      "name": "autoreply",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "local",
          "value": "frozprsn@onmicrosoft.example.com"
        },
        {
          "name": "sunetidpreferred",
          "value": "frozprsn"
        },
        {
          "name": "sunetid",
          "value": "frozprsn"
        },
        {
          "name": "sunetid",
          "value": "frozen.person"
        },
        {
          "name": "urirouteto",
          "value": "http://geocities.com/neworleans/12/11/"
        },
        {
          "name": "emailSystem",
          "value": "office365"
        }
      ],
      "name": "seas",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "principal",
          "value": "frozprsn"
        },
        {
          "name": "uid",
          "value": "12346"
        },
        {
          "name": "notgs",
          "value": "1"
        }
      ],
      "name": "kerberos",
      "status": "frozen"
    },
    {
      "settings": [
        {
          "name": "accounttype",
          "value": "personal"
        },
        {
          "name": "quota",
          "value": "1000"
        },
        {
          "name": "admin",
          "value": "frozprsn"
        }
      ],
      "name": "email",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "shell",
          "value": "/bin/bash"
        }
      ],
      "name": "leland",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "homedirectory",
          "value": "/afs/te/users/f/r/frozprsn"
        }
      ],
      "name": "afs",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "uid",
          "value": "12346"
        }
      ],
      "name": "pts",
      "status": "active"
    }
  ],
  "owner": "person/24c11a772540d9aec770213f3470e90dc",
  "type": "self",
  "name": "Person, Frozen",
  "id": "frozprsn",
  "description": "Staff - University IT",
  "status": "active",
  "url": "http://example.com/accounts/frozprsn",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_formerpsn = """
{
  "services": [
    {
      "settings": [
        {
          "name": "principal",
          "value": "formerpsn"
        }
      ],
      "name": "kerberos",
      "status": "inactive"
    },
    {
      "settings": [
        {
          "name": "shell",
          "value": "/bin/tcsh"
        }
      ],
      "name": "leland",
      "status": "inactive"
    }
  ],
  "owner": "person/10de823ca35c5e26beb825bf0e4521aff",
  "type": "self",
  "name": "Person, Former",
  "id": "formerpsn",
  "description": "Former Staff - University IT",
  "status": "inactive",
  "url": "http://example.com/accounts/formerpsn",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
"""

json_affilite = '''
{
  "services": [
    {
      "settings": [],
      "name": "dialin",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "local",
          "value": "affilite@zm88.example.com"
        },
        {
          "name": "sunetidpreferred",
          "value": "affilite"
        },
        {
          "name": "sunetid",
          "value": "affilite"
        }
      ],
      "name": "seas",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "principal",
          "value": "affilite"
        },
        {
          "name": "uid",
          "value": "12344"
        }
      ],
      "name": "kerberos",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "accounttype",
          "value": "personal"
        }
      ],
      "name": "email",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "shell",
          "value": "/bin/bash"
        }
      ],
      "name": "leland",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "homedirectory",
          "value": "/afs/te/users/a/f/affilite"
        }
      ],
      "name": "afs",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "uid",
          "value": "12344"
        }
      ],
      "name": "pts",
      "status": "active"
    }
  ],
  "owner": "person/6239304b8ed646e811737031c9187ce46",
  "type": "self",
  "name": "Smith, Affiliate",
  "id": "affilite",
  "description": "Affiliate - Genetics",
  "status": "active",
  "url": "http://example.com/accounts/affilite",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_afilbase = '''
{
  "services": [
    {
      "settings": [
        {
          "name": "principal",
          "value": "afilbase"
        },
        {
          "name": "uid",
          "value": "12333"
        }
      ],
      "name": "kerberos",
      "status": "active"
    }
  ],
  "owner": "person/b21b790eafc6531bdd85f505dc31bef1e",
  "type": "self",
  "name": "Jones, Base Affiliate",
  "id": "afilbase",
  "description": "Affiliate - Anesthesia",
  "status": "active",
  "url": "http://example.com/accounts/afilbase",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_functional = '''
{
  "services": [
    {
      "settings": [
        {
          "name": "principal",
          "value": "functional"
        },
        {
          "name": "uid",
          "value": "12332"
        }
      ],
      "name": "kerberos",
      "status": "active"
    },
    {
      "settings": [
        {
          "name": "uid",
          "value": "12332"
        }
      ],
      "name": "pts",
      "status": "active"
    }
  ],
  "owner": "organization/54ec803d070816db5f093db9faaf05fce",
  "type": "functional",
  "name": "Functional Account",
  "id": "functional",
  "description": "Functional Account",
  "status": "active",
  "url": "http://example.com/accounts/functional",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_oldfunctional = '''
{
  "services": [
    {
      "settings": [
        {
          "name": "principal",
          "value": "oldfunctional"
        }
      ],
      "name": "kerberos",
      "status": "inactive"
    }
  ],
  "owner": "organization/9bf85dea9188297fdd394fc758bf5908f",
  "type": "functional",
  "name": "Old Functional Account",
  "id": "oldfunctional",
  "description": "Functional Account",
  "status": "inactive",
  "url": "http://example.com/accounts/oldfunctional",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_sharedmailbox = '''
{
  "services": [
    {
      "settings": [
        {
          "name": "forward",
          "value": "sharedmailbox@onmicrosoft.example.com"
        },
        {
          "name": "sunetidpreferred",
          "value": "sharedmailbox"
        },
        {
          "name": "sunetid",
          "value": "sharedmailbox"
        }
      ],
      "name": "seas",
      "status": "active"
    }
  ],
  "owner": "organization/c3f6e1fc214a001f6714fccec0958dcab",
  "type": "functional",
  "name": "Some Group Mailbox - shared email",
  "id": "sharedmailbox",
  "description": "Shared mailbox for some group",
  "status": "active",
  "url": "http://example.com/accounts/sharedmailbox",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

# These are accounts that are weird (to us), in some way

json_newservice = '''
{
  "services": [
    {
      "settings": [
        {
          "name": "something",
          "value": "a"
        },
        {
          "name": "else",
          "value": "2"
        }
      ],
      "name": "zzzz",
      "status": "active"
    }
  ],
  "owner": "organization/54ec803d070816db5f093db9faaf05fce",
  "type": "functional",
  "name": "New Service Test Account",
  "id": "newservice",
  "description": "New Service Test Account",
  "status": "active",
  "url": "http://example.com/accounts/newservice",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

json_newtype = '''
{
  "services": [
    {
      "settings": [
        {
          "name": "something",
          "value": "a"
        },
        {
          "name": "else",
          "value": "2"
        }
      ],
      "name": "zzzz",
      "status": "active"
    }
  ],
  "owner": "organization/54ec803d070816db5f093db9faaf05fce",
  "type": "service",
  "name": "New Type of Account",
  "id": "newtype",
  "description": "New Type of Account",
  "status": "active",
  "url": "http://example.com/accounts/newtype",
  "statusDate": 1578036073000,
  "statusDateStr": "2020-01-03T15:14:13.00Z"
}
'''

# Add Accounts responses to the Responses mock session
def add_account_responses() -> None:
    # GET ACCOUNTS

    # Valid accounts

    responses.add(
        responses.GET,
        'http://example.com/accounts/fullprsn',
        status=200,
        content_type='application/json',
        body=json_fullprsn,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/frozprsn',
        status=200,
        content_type='application/json',
        body=json_frozprsn,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/formerpsn',
        status=200,
        content_type='application/json',
        body=json_formerpsn,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/affilite',
        status=200,
        content_type='application/json',
        body=json_affilite,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/afilbase',
        status=200,
        content_type='application/json',
        body=json_afilbase,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/functional',
        status=200,
        content_type='application/json',
        body=json_functional,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/oldfunctional',
        status=200,
        content_type='application/json',
        body=json_oldfunctional,
    )

    responses.add(
        responses.GET,
        'http://example.com/accounts/sharedmailbox',
        status=200,
        content_type='application/json',
        body=json_sharedmailbox,
    )

    # Account with an unknown service
    responses.add(
        responses.GET,
        'http://example.com/accounts/newservice',
        status=200,
        content_type='application/json',
        body=json_newservice,
    )

    # Account with an unknown type
    responses.add(
        responses.GET,
        'http://example.com/accounts/newtype',
        status=200,
        content_type='application/json',
        body=json_newtype,
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
        'http://example.com/accounts/frozen.person',
        status=404,
        content_type='application/json',
        json={
            'status': 404,
            'message': 'Account "frozen.person" does not exist',
            'url': 'http://example.com/accounts/frozen.person'
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
