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

import itertools
import pytest
import ssl
from stanford.mais.client import MAISClient

services = (
    'account',
    'course',
    'person',
    'privilege',
    'student',
    'workgroup',
)

# Test if we can make a PROD client, it has URLs defined, and we get a Session
def test_good_prod(snakeoil_cert):
    client = MAISClient.prod(snakeoil_cert)
    for service in services:
        assert service in client.urls

# Test the same with UAT.
def test_good_uat(snakeoil_cert):
    client = MAISClient.uat(snakeoil_cert)
    for service in services:
        assert service in client.urls

# Ensure we throw if we don't have any URLs, or we don't provide a mapping.
def test_no_urls(snakeoil_cert):
    with pytest.raises(TypeError):
        MAISClient(cert=snakeoil_cert)
    with pytest.raises(TypeError):
        MAISClient(cert=snakeoil_cert, urls=('https://localhost',))

# Ensure we throw if no certs are provided.
def test_no_certs():
    with pytest.raises(FileNotFoundError):
        MAISClient.prod(cert='/tmp/sdfsfdfmkdmksklfsdfdms')

# Test with a malformed combined cert/key file
def test_bad_certkey(tmpdir_factory):
    bad_path = tmpdir_factory.mktemp('bad_certkey') / 'bad.pem'
    bad_file = bad_path.open('w', encoding='ascii')
    bad_file.write('''
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
''')
    bad_file.close()
    with pytest.raises(ssl.SSLError):
        MAISClient.prod(cert=bad_path)
