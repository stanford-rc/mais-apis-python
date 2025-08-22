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
from stanford.mais.client import MAISClient
from stanford.mais.account import AccountClient, Account
from stanford.mais.account.validate import AccountValidationResults, validate

"""
This code tests everything in stanford.mais.account.validate.

For information on our test users, see the code in test_account_properties.py.
"""

# Check if each test user is (or is not) in the correct validation sets
def test_validate_collections(account_client):
    # Start with a good case:
    input_good_tuple = (
        'fullprsn',
        'frozprsn',
        'formerpsn',
        'affilite',
        'afilbase',
        'functional',
        'oldfunctional',
        'sharedmailbox',
        'nobody',
    )
    input_good_set = set(input_good_tuple)
    input_good_frozenset = frozenset(input_good_tuple)
    input_good_list = list(input_good_tuple)

    # Run validation on each input   
    validated_set = validate(input_good_set, account_client)
    validated_frozenset = validate(input_good_frozenset, account_client)
    validated_tuple = validate(input_good_tuple, account_client)
    validated_list = validate(input_good_list, account_client)

    # All the validation results should be identical
    assert validated_list == validated_tuple
    assert validated_list == validated_set

    # Since we've confirmed all the results are identical, we just need to
    # check one in detail.

    # We skip checking raw, because we don't have an input string.

    # Check raw_set matches
    # NOTE: We only know that raw_set is a Collection.
    # So, to avoid typing issues, and to avoid caring about order, explicitly
    # make raw_set into a set, and then check that against our set.
    assert set(validated_set.raw_set) == input_good_set

    # Check to see who is in full
    assert 'fullprsn' in validated_set.full
    assert 'frozprsn' in validated_set.full
    assert 'formerpsn' not in validated_set.full
    assert 'affilite' in validated_set.full
    assert 'afilbase' not in validated_set.full
    assert 'functional' not in validated_set.full
    assert 'oldfunctional' not in validated_set.full
    assert 'sharedmailbox' not in validated_set.full
    assert 'nobody' not in validated_set.full
    assert len(validated_set.full) == 3

    # Check to see who is in base
    assert 'baseprsn' not in validated_set.base
    assert 'frozprsn' not in validated_set.base
    assert 'formerpsn' not in validated_set.base
    assert 'affilite' not in validated_set.base
    assert 'afilbase' in validated_set.base
    assert 'functional' not in validated_set.base
    assert 'oldfunctional' not in validated_set.base
    assert 'sharedmailbox' not in validated_set.base
    assert 'nobody' not in validated_set.base
    assert len(validated_set.base) == 1

    # Check to see who is in inactive
    assert 'inactiveprsn' not in validated_set.inactive
    assert 'frozprsn' not in validated_set.inactive
    assert 'formerpsn' in validated_set.inactive
    assert 'affilite' not in validated_set.inactive
    assert 'afilbase' not in validated_set.inactive
    assert 'functional' not in validated_set.inactive
    assert 'oldfunctional' not in validated_set.inactive
    assert 'sharedmailbox' not in validated_set.inactive
    assert 'nobody' not in validated_set.inactive
    assert len(validated_set.inactive) == 1

    # Check to see who is in unknown
    # (Rememeber, functional accounts are unknown to the validation function)
    assert 'unknownprsn' not in validated_set.unknown
    assert 'frozprsn' not in validated_set.unknown
    assert 'formerpsn' not in validated_set.unknown
    assert 'affilite' not in validated_set.unknown
    assert 'afilbase' not in validated_set.unknown
    assert 'functional' in validated_set.unknown
    assert 'oldfunctional' in validated_set.unknown
    assert 'sharedmailbox' in validated_set.unknown
    assert 'nobody' in validated_set.unknown
    assert len(validated_set.unknown) == 4

# Test that, when presented with a string, `validate` handles different forms
# of whitespace separator.
def test_validate_string(account_client):
    # Start with a tuple of our SUNetIDs:
    input_good_tuple = (
        'fullprsn',
        'frozprsn',
        'formerpsn',
        'affilite',
        'afilbase',
        'functional',
        'oldfunctional',
        'sharedmailbox',
        'nobody',
    )

    # Make a set of strings, with different separators
    # These should all parse correctly
    input_good_string1 = ' '.join(input_good_tuple)
    input_good_string3 = ','.join(input_good_tuple)
    input_good_string4 = '\n'.join(input_good_tuple)
    input_good_string5 = '\r'.join(input_good_tuple)
    input_good_string6 = '\r\n'.join(input_good_tuple)
    input_good_string7 = '\t'.join(input_good_tuple)
    input_good_string8 = ','.join(input_good_tuple)

    # Run validation on each input   
    validated_string1 = validate(input_good_string1, account_client)
    validated_string3 = validate(input_good_string3, account_client)
    validated_string4 = validate(input_good_string4, account_client)
    validated_string5 = validate(input_good_string5, account_client)
    validated_string6 = validate(input_good_string6, account_client)
    validated_string7 = validate(input_good_string7, account_client)
    validated_string8 = validate(input_good_string8, account_client)

    # All the validation results should be identical, but we can't do a simple
    # comparison, because `raw` will be different for each.
    def is_equal(
        a: AccountValidationResults,
        b: AccountValidationResults,
    ) -> None:
        assert a.raw_set == b.raw_set
        assert a.full == b.full
        assert a.base == b.base
        assert a.inactive == b.inactive
        assert a.unknown == b.unknown
    is_equal(validated_string1, validated_string3)
    is_equal(validated_string1, validated_string4)
    is_equal(validated_string1, validated_string5)
    is_equal(validated_string1, validated_string6)
    is_equal(validated_string1, validated_string7)
    is_equal(validated_string1, validated_string8)

    # Check that the raw string matches the input
    assert validated_string1.raw == input_good_string1
    assert validated_string3.raw == input_good_string3
    assert validated_string4.raw == input_good_string4
    assert validated_string5.raw == input_good_string5
    assert validated_string6.raw == input_good_string6
    assert validated_string7.raw == input_good_string7
    assert validated_string8.raw == input_good_string8

    # Check to see who is in full
    assert 'fullprsn' in validated_string1.full
    assert 'frozprsn' in validated_string1.full
    assert 'formerpsn' not in validated_string1.full
    assert 'affilite' in validated_string1.full
    assert 'afilbase' not in validated_string1.full
    assert 'functional' not in validated_string1.full
    assert 'oldfunctional' not in validated_string1.full
    assert 'sharedmailbox' not in validated_string1.full
    assert 'nobody' not in validated_string1.full
    assert len(validated_string1.full) == 3

    # Check to see who is in base
    assert 'baseprsn' not in validated_string1.base
    assert 'frozprsn' not in validated_string1.base
    assert 'formerpsn' not in validated_string1.base
    assert 'affilite' not in validated_string1.base
    assert 'afilbase' in validated_string1.base
    assert 'functional' not in validated_string1.base
    assert 'oldfunctional' not in validated_string1.base
    assert 'sharedmailbox' not in validated_string1.base
    assert 'nobody' not in validated_string1.base
    assert len(validated_string1.base) == 1

    # Check to see who is in inactive
    assert 'inactiveprsn' not in validated_string1.inactive
    assert 'frozprsn' not in validated_string1.inactive
    assert 'formerpsn' in validated_string1.inactive
    assert 'affilite' not in validated_string1.inactive
    assert 'afilbase' not in validated_string1.inactive
    assert 'functional' not in validated_string1.inactive
    assert 'oldfunctional' not in validated_string1.inactive
    assert 'sharedmailbox' not in validated_string1.inactive
    assert 'nobody' not in validated_string1.inactive
    assert len(validated_string1.inactive) == 1

    # Check to see who is in unknown
    # (Rememeber, functional accounts are unknown to the validation function)
    assert 'unknownprsn' not in validated_string1.unknown
    assert 'frozprsn' not in validated_string1.unknown
    assert 'formerpsn' not in validated_string1.unknown
    assert 'affilite' not in validated_string1.unknown
    assert 'afilbase' not in validated_string1.unknown
    assert 'functional' in validated_string1.unknown
    assert 'oldfunctional' in validated_string1.unknown
    assert 'sharedmailbox' in validated_string1.unknown
    assert 'nobody' in validated_string1.unknown
    assert len(validated_string1.unknown) == 4
