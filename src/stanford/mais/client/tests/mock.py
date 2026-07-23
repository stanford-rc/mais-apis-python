# vim: ts=4 sw=4 et
# -*- coding: utf-8 -*-

# © 2026 The Board of Trustees of the Leland Stanford Junior University.
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
import base64
import dataclasses

# PyPi imports
import responses

# Make some test data!

json_token = '''
{
  "access_token":"abcdef123",
  "token_type":"Bearer",
  "expires_in":3600
}
'''

json_invalid_client = '''
{
  "error":"invalid_client"
}
'''

json_invalid_client_secret = '''
{
  "error":"invalid_client: invalid_client_secret"
}
'''

def authorization_header(
    client_id: str,
    client_secret: str,
) -> dict[str, str]:
    raw_string = (
        client_id.encode('ASCII')
        + b':'
        + client_secret.encode('ASCII')
    )
    base64_bytes = base64.b64encode(raw_string)
    return {
        "Authorization": "Basic " + base64_bytes.decode('ASCII'),
    }

# Add OAuth Token responses to the Responses mock session
def add_token_responses() -> None:
    # A successful token request
    responses.add(
        responses.POST,
        'http://example.com/oauth2/token',
        match=[
            responses.matchers.header_matcher(
                authorization_header('good1', 'good2')
            ),
            responses.matchers.urlencoded_params_matcher({
                'grant_type': 'client_credentials',
            }),
        ],
        status=200,
        content_type='application/json',
        body=json_token,
    )

    # A token request with a bad client_id
    responses.add(
        responses.POST,
        'http://example.com/oauth2/token',
        match=[
            responses.matchers.header_matcher(
                authorization_header('good', 'bad')
            ),
            responses.matchers.urlencoded_params_matcher({
                'grant_type': 'client_credentials',
            }),
        ],
        status=400,
        content_type='application/json',
        body=json_invalid_client,
    )

    # A token request with a bad client_secret
    responses.add(
        responses.POST,
        'http://example.com/oauth2/token',
        match=[
            responses.matchers.header_matcher(
                authorization_header('bad', 'good')
            ),
            responses.matchers.urlencoded_params_matcher({
                'grant_type': 'client_credentials',
            }),
        ],
        status=400,
        content_type='application/json',
        body=json_invalid_client_secret,
    )

    # All done!
    return None
