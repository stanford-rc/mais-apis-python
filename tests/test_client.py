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

# Test if we can get a client with separate key and cert
def test_good_prod_certkey(snakeoil_cert_key):
    client = MAISClient.prod(
        cert=snakeoil_cert_key[0],
        key=snakeoil_cert_key[1],
    )
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
        MAISClient.prod(cert='/tmp/sdfsfdfmkdmksklfsdfdms') # nosec: B108

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

# Test with a malformed cert file but good key file
def test_bad_cert_good_key(tmpdir_factory):
    bad_cert_good_key_path = tmpdir_factory.mktemp('bad_cert_good_key')
    bad_cert_path = bad_cert_good_key_path / 'bad_cert.pem'
    good_key_path = bad_cert_good_key_path / 'good_key.pem'
    bad_cert_file = bad_cert_path.open('w', encoding='ascii')
    good_key_file = good_key_path.open('w', encoding='ascii')
    bad_cert_file.write('''
-----BEGIN CERTIFICATE-----
MIIBSTCB76ADAgECAhRN+mw8yUTAU0ENSqkoKaZhxkyhsjAKBggqhkjOPQQDAjAT
MREwDwYDVQQDDAhzbmFrZW9pbDAeFw0yNTA2MjEyMDQwMDNaFw00NTA2MjEyMDQw
MDNaMBMxETAPBgNVBAmMCHNuYWtlb2lsMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcD
QgAEtGcgWywoqw66S1uHCOQkutdqMEBOeoSvoTUX+wvg8MZBfihTmLNO6zrlqMo+
QPrEgQaVfcYReeuJIGvn+DKk8KMhMB8wHQYDVR0OBBYEFMVhS8qvRIN1CTZj757M
o0xg0txhMAoGCCqGSM49BAMCA0kAMEYCIQCp9eFScWdO0UyNMbqsG4mXez6ALY88
H8lmT6mVTkHJOAIhAO1ayGcZKq1TI3DIpaNJHCWKAuUY5BLurfChzSvQSrDB
-----END CERTIFICATE-----
''')
    good_key_file.write('''
-----BEGIN EC PARAMETERS-----
BggqhkjOPQMBBw==
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEIDI9ntYm7msj7i9+DIM2D+ShZnSTxICDncOV1wFAlEijoAoGCCqGSM49
AwEHoUQDQgAEtGcgWywoqw66S1uHCOQkutdqMEBOeoSvoTUX+wvg8MZBfihTmLNO
6zrlqMo+QPrEgQaVfcYReeuJIGvn+DKk8A==
-----END EC PRIVATE KEY-----
''')
    bad_cert_file.close()
    good_key_file.close()
    with pytest.raises(ssl.SSLError):
        MAISClient.prod(
            cert=bad_cert_path,
            key=good_key_path,
        )

# Test with a good cert but bad key file
def test_good_cert_bad_key(tmpdir_factory):
    good_cert_bad_key_path = tmpdir_factory.mktemp('good_cert_bad_key')
    good_cert_path = good_cert_bad_key_path / 'good_cert.pem'
    bad_key_path = good_cert_bad_key_path / 'bad_key.pem'
    good_cert_file = good_cert_path.open('w', encoding='ascii')
    bad_key_file = bad_key_path.open('w', encoding='ascii')
    good_cert_file.write('''
-----BEGIN CERTIFICATE-----
MIIBSDCB76ADAgECAhQN8DYs3urHr5LXpviDtiR8xQMG1jAKBggqhkjOPQQDAjAT
MREwDwYDVQQDDAhzbmFrZW9pbDAeFw0yNTA2MjEyMDQwMDFaFw00NTA2MjEyMDQw
MDFaMBMxETAPBgNVBAMMCHNuYWtlb2lsMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcD
QgAEGUOrb6DaRgG9g0YUwyZ/+Xl4z8LTHTeHXjVuBqzu1kjvhy1Tg21Znux9GN0P
h5vkIQgG2jb2MW2Eq729iT6zD6MhMB8wHQYDVR0OBBYEFD8l9ywR8EYYDNnGfUlh
3ZlDxw+dMAoGCCqGSM49BAMCA0gAMEUCICnCq8kbLVnWKFSp4TcA7lQo2XXjfgVp
h0kkK0s3hoxMAiEAuJF9yRNgOwdLaUonyJ3iTT8kye30QbxP+wx8QGc/ayw=
-----END CERTIFICATE-----
''')
    bad_key_file.write('''
-----BEGIN EC PARAMETERS-----
BggqhkjOPQMBBw==
-----END EC PARAMETERS-----
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEII47Xsvzg4TxGjoz/ftPJ/Zfw3aEo6Og3SqPYA8zeqFfoAoGCCqGSM49
AwEHoUQDQgAEGUOrb6DaRgG9g0YUwyZ/+Xl4z8LTHTEHXjVuBqzu1kjvhy1Tg21Z
nux9GN0Ph5vkIQgG2jb2MW2Eq729iT6zDw==
-----END EC PRIVATE KEY-----
''')
    good_cert_file.close()
    bad_key_file.close()
    with pytest.raises(ssl.SSLError):
        MAISClient.prod(
            cert=good_cert_path,
            key=bad_key_path,
        )
