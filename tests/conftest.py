# vim: ts=4 sw=4 et
# -*- coding: utf-8 -*-

# © 2021 The Board of Trustees of the Leland Stanford Junior University.
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

import pytest

# These are fixtures that will be used in various tests.

# This is a "snakeoil" key and cert that can be used whenever MAISClient needs
# a valid key & cert.
# If you want to make a one, `test_cert_create.sh` can help!
@pytest.fixture(scope='session')
def snakeoil_cert(tmpdir_factory):
    snakeoil_path = tmpdir_factory.mktemp('certs') / 'snakeoil.pem'
    snakeoil_file = snakeoil_path.open('w', encoding='ascii')
    snakeoil_file.write('''
-----BEGIN EC PARAMETERS-----
BggqhkjOPQMBBw==
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEILXkVDzoQTChgDgY0hOmVefCHjmBB6Mjlez4Zyk/pqdNoAoGCCqGSM49
AwEHoUQDQgAEYpieO/7CHnAB/nU6cmgwuiHDCKirtNIxlY0IMsUctst/rWahkHmt
o2/9Qwa9U4QqBbfUsrOB9Aj14U62VK2C2A==
-----END EC PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIIBHzCBxwIUIKCkNzLR2prWEb/cu8zSAVj7QskwCgYIKoZIzj0EAwIwEzERMA8G
A1UEAwwIc25ha2VvaWwwHhcNMjEwNjI2MDIxMzE4WhcNNDEwNjI2MDIxMzE4WjAT
MREwDwYDVQQDDAhzbmFrZW9pbDBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABGKY
njv+wh5wAf51OnJoMLohwwioq7TSMZWNCDLFHLbLf61moZB5raNv/UMGvVOEKgW3
1LKzgfQI9eFOtlStgtgwCgYIKoZIzj0EAwIDRwAwRAIgdJnUKczm8XAYZX8wGQ0H
sAyGGkZVw52AnLoAOH1sqwwCIDM0TW7Oas8ZA7YdO7RLCYcOsLQyleOywuXepDmt
R0XW
-----END CERTIFICATE-----
''')
    snakeoil_file.close()
    return snakeoil_path

# This creates separate key and cert parameters, to test constructing a
# MAISClient with separate files.
@pytest.fixture(scope='session')
def snakeoil_cert_key(tmpdir_factory):
    snakeoil_path = tmpdir_factory.mktemp('cert_key')
    snakeoil_key_path = snakeoil_path / 'snakeoil.key'
    snakeoil_cert_path = snakeoil_path / 'snakeoil.pem'
    snakeoil_key_file = snakeoil_key_path.open('w', encoding='ascii')
    snakeoil_cert_file = snakeoil_cert_path.open('w', encoding='ascii')
    snakeoil_key_file.write('''
-----BEGIN EC PARAMETERS-----
BggqhkjOPQMBBw==
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEILXkVDzoQTChgDgY0hOmVefCHjmBB6Mjlez4Zyk/pqdNoAoGCCqGSM49
AwEHoUQDQgAEYpieO/7CHnAB/nU6cmgwuiHDCKirtNIxlY0IMsUctst/rWahkHmt
o2/9Qwa9U4QqBbfUsrOB9Aj14U62VK2C2A==
-----END EC PRIVATE KEY-----
''')
    snakeoil_cert_file.write('''
-----BEGIN CERTIFICATE-----
MIIBHzCBxwIUIKCkNzLR2prWEb/cu8zSAVj7QskwCgYIKoZIzj0EAwIwEzERMA8G
A1UEAwwIc25ha2VvaWwwHhcNMjEwNjI2MDIxMzE4WhcNNDEwNjI2MDIxMzE4WjAT
MREwDwYDVQQDDAhzbmFrZW9pbDBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IABGKY
njv+wh5wAf51OnJoMLohwwioq7TSMZWNCDLFHLbLf61moZB5raNv/UMGvVOEKgW3
1LKzgfQI9eFOtlStgtgwCgYIKoZIzj0EAwIDRwAwRAIgdJnUKczm8XAYZX8wGQ0H
sAyGGkZVw52AnLoAOH1sqwwCIDM0TW7Oas8ZA7YdO7RLCYcOsLQyleOywuXepDmt
R0XW
-----END CERTIFICATE-----
''')
    snakeoil_key_file.close()
    snakeoil_cert_file.close()
    return (snakeoil_cert_path, snakeoil_key_path)

# For tests that require a good MAIS client, return one.
# NOTE: As tests are made for additional services, add those URLs here.
@pytest.fixture(scope='session')
def mais_client(snakeoil_cert):
    return MAISClient.uat(cert=snakeoil_cert, urls={
        'account': 'https://localhost/account/',
    })

# For tests that require a good Account API client, return one.
@pytest.fixture(scope='session')
def account_client(mais_client):
    return AccountClient(client=mais_client)
