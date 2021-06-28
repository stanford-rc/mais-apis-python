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

import dataclasses
import logging
from typing import *

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info

__all__ = (
    'AccountService',
    'AccountServiceKerberos',
    'AccountServiceLibrary',
    'AccountServiceSEAS',
    'AccountServiceEmail',
    'AccountServiceAutoreply',
    'AccountServiceLeland',
    'AccountServicePTS',
    'AccountServiceAFS',
    'AccountServiceDialin',
)

# Each account service has a different class.  Combine that with the base
# class, and you've got enough stuff to put into its own file!
# Start with the base class, and then move on to the subclasses.
# Classes appear in this file in `__all__` order.

@dataclasses.dataclass(frozen=True)
class AccountService():
    """Represents an account service.

    This is a base container representing a service, and stores the
    common properties that a service can have.  For service-specific
    properties, check out the documentation for the appropriate subclasses.
    """

    name: str
    """
    The name of the service.
    """

    is_active: bool
    """
    ``True`` if the service is active for the associated account.
    """

    # This really should be marked as an @abc.abstractclass, but MyPy raises an
    # error because of https://github.com/python/mypy/issues/5374
    @classmethod
    def _from_json(
        cls,
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ):
        raise NotImplementedError('AccountService._from_json() must be implemented in all subclasses.')

    @staticmethod
    def _json_to_dict(
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> Dict[str, Any]:
        """Given a dict parsed from JSON, extract all of the service keys we
        recognize.

        This is used when we are building a new instance, and only pulls out
        the common stuff.  It ignores 
        """
        return {
            'name': source['name'],
            'is_active': (True if source['status'] == "active" else False),
        }

    @staticmethod
    def _get_setting(
        settings: List[Dict[str, str]],
        target: str
    ) -> Union[None, str, Set[str]]:
        """Convenience method to pull a setting out of a settings dict.

        :returns: If the setting was single-valued, return it as a string.  If the setting was multi-valued, return a set of strings.  If the setting was not found, return None.
        """
        results = set()
        for setting in settings:
            if setting['name'] == target:
                results.add(setting['value'])
        if len(results) == 0:
            return None
        elif len(results) == 1:
            return results.pop()
        else:
            return results

    OptionalTupleOfStrings = Union[Tuple[()], Tuple[str, ...]]
    @staticmethod
    def _get_settings(
        source: Dict[str, Union[str, List[Dict[str, str]]]],
        service: str,
        required_keys_single: OptionalTupleOfStrings = tuple(),
        required_keys_multiple: OptionalTupleOfStrings = tuple(),
        optional_keys_single: OptionalTupleOfStrings = tuple(),
        optional_keys_multiple: OptionalTupleOfStrings = tuple(),
    ) -> Dict[str, Union[None, str, Set[str]]]:
        """Convenience method to pull settings out of a settings dict

        :param source: The dict for a single service, taken from the JSON array of services returned by the Account API.

        :param service: The name of the service, used when raising exceptions.

        :param required_keys_single: The single-valued fields which must be present in an active service.

        :param required_keys_multiple: The multi-valued fields which must be present in an active service.

        :param optional_keys_single: The single-valued fields which *may* be present in an active service.

        :param optional_keys_multiple: The multi-valued fields which *may* be present in an active service.

        :returns: A dict, suitable for passing to the dataclass constructor (once ``name`` and ``is_active`` are included).

        :raises KeyError: A required setting is missing.

        :raises TypeError: The 'settings' list is not actually a list.
        """
        result: Dict[str, Union[None, str, Set[str]]] = dict()

        # Is this account inactive?  If yes, all keys are optional.
        if source['status'] != 'active':
            optional_keys_single += required_keys_single
            optional_keys_multiple += required_keys_multiple
            required_keys_single = tuple()
            required_keys_multiple = tuple()

        # Make sure our settings list is a list.
        # (Needed because we can't be sure with the type-checker.)
        if isinstance(source['settings'], list):
            settings = source['settings']
        else:
            raise TypeError(f"Service {service} has a non-list 'settings'")

        # Add all keys, required and optional
        for k in (
            required_keys_single + required_keys_multiple +
            optional_keys_single + optional_keys_multiple
        ):
            result[k] = AccountService._get_setting(settings, k)

        # Error out if a required key is missing
        for k in (required_keys_single + required_keys_multiple):
            if result[k] is None:
                raise KeyError(f"Service {service} missing required setting {k}")

        # Ensure multi-value keys are in sets
        for k in (required_keys_multiple + optional_keys_multiple):
            should_be_set = result[k]
            if isinstance(should_be_set, str):
                result[k] = set([should_be_set])

        # All done!
        return result

@dataclasses.dataclass(frozen=True)
class AccountServiceKerberos(AccountService):
    """``kerberos`` service for an Account.

    This represents an account's entry in Kerberos.  If active, then the
    account is at least a base (or base-sponsored) account.
    """

    principal: str
    """
    The name of the Kerberos principal.  This is normally the same as the
    SUNetID.
    """

    uid: int
    """
    The UNIX UID number.

    .. note::
       This is used as the account's ``uidNumber`` in LDAP.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceKerberos'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceKerberos':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'kerberos',
            required_keys_single = ('principal',),
            optional_keys_single = ('uid',),
        ))

        # Convert uid to an int
        if kwargs['uid'] is not None:
            kwargs['uid'] = int(kwargs['uid'])

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceLibrary(AccountService):
    """``library`` service for an Account.

    `New as of 2019`_, this represents access to `Library e-resources`_.  It
    has no known settings, and you should *not* assume that having this enabled
    means the account is full or full-sponsored.

    .. _New as of 2019: https://uit.stanford.edu/service/sponsorship/sponsor-library-e-resources

    .. _Library e-resources: https://uit.stanford.edu/service/sponsorship/sponsor-library-e-resources
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceLibrary'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceLibrary':
        # We don't have any settings.  Pull out common stuff and return.
        kwargs = cls._json_to_dict(source)
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceSEAS(AccountService):
    """``seas`` service for an Account.

    The "Stanford Electronic Alias Service".  If this service is active, then
    the account has an associated `@stanford.edu` email address, even if they
    don't have a Stanford email box.

    .. note::
       Even though they include a shared mailbox, `Shared Email`_ functional
       accounts have ``seas`` service, but not ``email`` service.

    .. _Shared Email: https://uit.stanford.edu/service/sharedemail
    """

    local: str
    """
    This is an optional setting.  If the account has a Stanford email box,
    *and* the account wants emails delivered to that mailbox, then this is the
    this is the canonical email address for that mailbox.

    .. warning::
       Do not try to send emails directly to this email address.
    """

    sunetid: str
    """
    This is a setting which may appear multiple times.  Each entry represents
    an `@stanford.edu` email address.  There will always be one entry matching
    the account's ID (so that `id@stanford.edu` works).  If the user has any
    email alises, each alias will appear as an additional entry.
    """

    sunetidpreferred: str
    """
    This is the alias that the user prefers to use as their ID in their
    Stanford email address.  If the user does not have any aliases,
    then this will be their account ID.

    .. note::
       This setting, along with the tier-specific suffix (``@stanford.edu`` on
       PROD), is used for the user's ``mail`` attribute in LDAP (in the
       ``people`` tree).
    """

    forward: str
    """
    This is an optional setting.  If present, emails received by this address
    will be forwarded to the emails listed in this setting.  Multiple emails
    are separated by a comma.

    .. warning::
       Do not try to send emails directly to this email address.
    """

    urirouteto: str
    """
    When a client browses to `<https://stanford.edu/~id>`_, this is the URI
    where the client will be redirected.  If it is just a path (and not a full
    URL), it is relative to `<https://web.stanford.edu/>`_.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceSEAS'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceSEAS':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'seas',
            required_keys_single = ('sunetidpreferred',),
            required_keys_multiple = ('sunetid',),
            optional_keys_single = ('local', 'forward', 'urirouteto'),
        ))

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceEmail(AccountService):
    """``email`` service for an Account.

    This represents a Stanford mailbox.  If active, the account has a Stanford
    electronic mailbox.  The ``seas`` service should also be present and
    active.

    .. note::
       The specific email backend (Zimbra, Office 365, Google, …) is not
       indicated.
    """

    accounttype: str
    """
    For people, this is ``personal``.  It *should not be used*.
    """

    quota: int
    """
    This setting was specific to the Zimbra backend, and *should not be used*.
    It may disappear in the future.
    """

    admin: str
    """
    This setting is obsolete, and *should not be used*.  It may disappear in
    the future.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceEmail'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceEmail':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'email',
            required_keys_single = ('accounttype',),
            optional_keys_single = ('quota', 'admin'),
        ))

        # Convert quota to an int
        if kwargs['quota'] is not None:
            kwargs['quota'] = int(kwargs['quota'])

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceAutoreply(AccountService):
    """``autoreply`` service for an Account.

    This represents the email autoresponder service.  If active, incoming
    emails will be forwarded to the autoresponder service, which will send an
    appropriate reply.
    """

    forward: str
    """
    The account's canonical email address in the autoresponder system.

    .. warning::
       Do not try to send emails directly to this email address.
    """

    subj: str
    """
    The subject line for the response.  The string ``$SUBJECT``, if present,
    will be replaced with the subject line from the incoming email.
    """

    msg: str
    """
    The contents of the response.  The string ``$SUBJECT``, if present, will be
    replaced with the subject line from the incoming email.  Also, the strings
    ``\\r`` and ``\\n`` represent a carriage return and line feed character,
    respectively.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceAutoreply'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceAutoreply':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'autoreply',
            required_keys_single = ('forward', 'subj', 'msg'),
        ))

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceLeland(AccountService):
    """``leland`` service for an Account.

    This represents the Stanford `Shared Computing`_ environment, originally
    known as `Leland`_ and known today as `FarmShare`_.  If active, users are
    able to log in to FarmShare.

    .. note::
       Full and full-sponsored accounts have this active; base and
       base-sponsored account do not.  Functional accounts never have this
       active.

    .. _Shared Computing: https://uit.stanford.edu/service/sharedcomputing
    .. _Leland: http://web.archive.org/web/20030728213702/http://lelandsystems.stanford.edu/
    .. _FarmShare: https://farmshare.stanford.edu/
    """

    shell: str
    """
    The absolute path to the user's login shell.

    .. warning::
       Active accounts that use the default shell do not have this set.  The
       default shell was originally ``/bin/tcsh``, but changed to
       ``/bin/bash``.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceLeland'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceLeland':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'leland',
            optional_keys_single = ('shell',),
        ))

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServicePTS(AccountService):
    """``pts`` service for an Account.

    This represents an account's entry in the AFS Protection Server's database.
    An account must have an entry here in order to access *any* AFS services.
    """

    uid: int
    """
    The UID number for the account in PTS.  It should be the same as the
    account's UID number in Kerberos.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServicePTS'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServicePTS':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'pts',
            required_keys_single = ('uid',),
        ))

        # Convert uid to an int
        if kwargs['uid'] is not None:
            kwargs['uid'] = int(kwargs['uid'])

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceAFS(AccountService):
    """``afs`` service for an Account.

    This represents an account's AFS home directory.
    """

    homedirectory: str
    """
    The path to the account's home directory.

    .. note::
       This is used as the account's `homeDirectory` in LDAP.  As such, you
       will probably want to override it.

    .. note::
       This setting assumes that AFS is mounted at path ``/afs`` on a ssytem.
       This is normally, but not always, the case.
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceAFS'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceAFS':
        # Start by pulling out the common stuff
        kwargs = cls._json_to_dict(source)

        # Add service-specific settings.
        kwargs.update(cls._get_settings(
            source = source,
            service = 'afs',
            required_keys_single = ('homedirectory',),
        ))

        # Call the constructor and return!
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceDialin(AccountService):
    """``dialin`` service for an Account.

    This represented the Stanford UIT dial-in modem pools, which had various
    phone numbers, including +1 (415) `498-1440`_ (this was before `area code
    650`_) and +1 (650) `325-1010`_.  If this service was active, you had
    access to the pool.  It has no settings, and *should not be used*.  If may
    disappear in the future.

    .. _498-1440: https://web.archive.org/web/19970205070531/http://commserv.stanford.edu/144.html

    .. _area code 650: https://web.archive.org/web/19970205070311/http://commserv.stanford.edu/CS.commnews.html

    .. _325-1010: https://web.archive.org/web/20000818114817/http://commserv.stanford.edu/modem/
    """

    @classmethod
    def _from_json(
        cls: Type['AccountServiceDialin'],
        source: Dict[str, Union[str, List[Dict[str, str]]]],
    ) -> 'AccountServiceDialin':
        # We don't have any settings.  Pull out common stuff and return.
        kwargs = cls._json_to_dict(source)
        return cls(**kwargs)
