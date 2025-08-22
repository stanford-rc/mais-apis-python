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

# This file has some references to classes that are defined in the same
# file.  Pythons older than 3.14 (which implements PEP 649) cannot handle that
# natively without this import.
# NOTE: At some point in the future, this annodation will be deprecated.
from __future__ import annotations

# Start with stdlib imports
import abc
import dataclasses
import enum
import logging
from typing import Any, Union

# Set up logging
logger = logging.getLogger(__name__)
debug = logger.debug
info = logger.info

__all__ = (
    'ServiceStatus',
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

# A service can have one of three different statuses
@enum.unique
class ServiceStatus(enum.Enum):
    """The possible statuses of a service.
    """

    ACTIVE = 'active'
    """The account has and can use this service.
    """

    FROZEN = 'frozen'
    """The account has this service, but it is inaccessible right now.

    .. note::
       Not every service uses this status.
    """

    INACTIVE = 'inactive'
    """The account does not have this service.

    .. note::
       The account may have had the service in the past, but does not now.  For
       example, full SUNetIDs have access to the autoreply service, but when
       autoreply is not enabled, the service is inactive.
    """

# Each account service has a different class.  Combine that with the base
# class, and you've got enough stuff to put into its own file!
# Start with the base class, and then move on to the subclasses.
# Classes appear in this file in `__all__` order.

@dataclasses.dataclass(frozen=True)
class AccountService(abc.ABC):
    """The base class for all account services.

    This is a base class representing a service, and stores the common
    properties that a service can have (the :data:`~AccountService.name` of the
    service, and its :data:`~AccountService.status`).  For service-specific
    properties, check out the documentation for the appropriate subclasses.
    """

    name: str
    """
    The name of the service.
    """

    status: ServiceStatus
    """
    The service's status.
    """

    @property
    def is_active(self) -> bool:
        """
        ``True`` if the service is active.

        .. danger::
           This will return `True` only when the service is active, *not when
           the service is frozen*.

           For some services, you might not care if the service is frozen.  For
           example, if an account's kerberos service is frozen, you might want
           to keep them in the directory, even if you don't want to allow
           logins.
        """
        return (True if self.status == ServiceStatus.ACTIVE else False)

    @property
    def not_inactive(self) -> bool:
        """
        ``True`` if the service is not inactive.

        This will return `True` when the service is active or frozen.  If the
        service is inactive, it will return `False`.
        """
        return (True if self.status != ServiceStatus.INACTIVE else False)

    @classmethod
    @abc.abstractmethod
    def _from_json(
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ):
        """Instantiate a service using a JSON-sourced dict.

        This class method must be implemented by each service's own subclass.
        The class method is responsible for taking a JSON-sourced dict,
        extracting the items specific to the service, and then calling the
        class constructor ``cls``.

        To help subclasses do their work, this class provides two static
        methods:

        * :meth:`_json_to_dict` takes the JSON-sourced dict, and extracts the
          attributes common to every service.  It's a good way to start
          building the dict of keyword arguments that will be passed through to
          the class constructor.

        * :meth:`_get_settings` is used by services that have a ``settings``
          dict in their JSON.  It supports mandatory & optional settings, and
          single- & multi-valued settings.  Not all services use this.
        """
        ...

    @staticmethod
    def _json_to_dict(
        source: dict[str, str | list[dict[str, str]]],
    ) -> dict[str, Any]:
        """Given a dict parsed from JSON, extract all of the service keys we
        recognize.

        This is used when we are building a new instance, and only pulls out
        the attributes that every service has (the service name, and service
        status).

        This convenience static method is used by all of the services.  The
        most-simple services use this method to pull common attributes from the
        JSON dict, and then immediately pass that to the class
        constructor.  Larger services start with this method's returned dict,
        and then either add dict items directly, or using `_get_settings` to
        extract items from the JSON dict.
        """
        return {
            'name': source['name'],
            'status': ServiceStatus(source['status']),
        }

    @staticmethod
    def _get_setting(
        settings: list[dict[str, str]],
        target: str
    ) -> None | str | set[str]:
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

    OptionalTupleOfStrings = Union[tuple[()], tuple[str, ...]]
    @staticmethod
    def _get_settings(
        source: dict[str, str | list[dict[str, str]]],
        service: str,
        required_keys_single: OptionalTupleOfStrings = tuple(),
        required_keys_multiple: OptionalTupleOfStrings = tuple(),
        optional_keys_single: OptionalTupleOfStrings = tuple(),
        optional_keys_multiple: OptionalTupleOfStrings = tuple(),
    ) -> dict[str, None | str | set[str]]:
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
        result: dict[str, None | str | set[str]] = dict()

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

    This represents an account's entry in Kerberos.  If an account has this
    service, then the account is at least a base (or base-sponsored) account.
    """

    principal: str
    """
    The name of the Kerberos principal.  This is normally the same as the
    SUNetID.

    .. note::
       This is an un-scoped principal.  In other words, it does not contain a
       Kerberos realm (because Stanford has multiple Kerberos realms!).
    """

    uid: int
    """
    The UNIX UID number.

    .. note::
       This is used as the account's ``uidNumber`` in LDAP.
    """

    @classmethod
    def _from_json(
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceKerberos:
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
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceLibrary:
        # We don't have any settings.  Pull out common stuff and return.
        kwargs = cls._json_to_dict(source)
        return cls(**kwargs)

@dataclasses.dataclass(frozen=True)
class AccountServiceSEAS(AccountService):
    """``seas`` service for an Account.

    The "Stanford Electronic Alias Service".  If this service is active, then
    the account has an associated *@stanford.edu* email address, even if they
    don't have a Stanford email box.

    .. note::
       Even though they include a shared mailbox, `Shared Email`_ functional
       accounts have ``seas`` service, but not ``email`` service.

    .. _Shared Email: https://uit.stanford.edu/service/sharedemail
    """

    local: str | None
    """
    This is an optional setting.  If the account has a Stanford email box,
    *and* the account wants emails delivered to that mailbox, then this is the
    this is the canonical email address for that mailbox.

    .. warning::
       Do not try to send emails directly to this email address.
    """

    sunetid: list[str]
    """
    This is a setting which may appear multiple times.  Each entry represents
    an `@stanford.edu` email address.  There will always be one entry matching
    the account's ID (so that ``id@stanford.edu`` works).  If the user has any
    email alises, each alias will appear as an additional entry.

    .. danger::
       Do not use this to look up an account's SUNetID/uid!
    """

    sunetidpreferred: str
    """
    One of the entries from :data:`~AccountServiceSEAS.sunetid`, this is the
    alias the the person prefers others use for email comunication.

    .. note::
       This setting, along with the tier-specific suffix (``@stanford.edu`` in
       PROD), is used for the user's ``mail`` attribute in LDAP (which you can
       find in the `people tree`_).

    .. _people tree: https://uit.stanford.edu/service/directory/datadefs/people
    """

    forward: str | None
    """
    This is an optional setting.  If present, emails received by this account
    will be forwarded to the emails listed in this setting.  Multiple emails
    are separated by a comma.

    .. warning::
       Do not try to send emails directly to this email address.
    """

    urirouteto: str
    """
    When a user points their web browser to to `<https://stanford.edu/~id>`_,
    this is the URI where the client will be redirected.  If it is just a path
    (not a full URL), it is relative to `<https://web.stanford.edu/>`_.
    """

    @classmethod
    def _from_json(
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceSEAS:
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

    If active, the account has a Stanford electronic mailbox.  The ``seas``
    service should also be present and active.

    .. note::
       The specific email backend (Zimbra, Office 365, Google, …) is not
       indicated.
    """

    accounttype: str
    """
    For people, this is ``personal``.  It *should not be used*.
    """

    quota: int | None
    """
    This setting was specific to the Zimbra backend, and *should not be used*.
    It may disappear in the future.
    """

    admin: str | None
    """
    This setting is obsolete, and *should not be used*.  It may disappear in
    the future.
    """

    @classmethod
    def _from_json(
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceEmail:
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

    This **used to** represent the email autoresponder service.  If active, incoming
    emails would have been forwarded to the autoresponder service, which would send an
    appropriate reply.

    In May 2025, the central autoresponder service `was turned off
    <https://uit.stanford.edu/news/stanford-accounts-getting-new-look>`_.
    Autoreply is now managed within the user's email system (Office 365, GMail,
    etc.).  This service may disappear in the future.
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
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceAutoreply:
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

    This represents the Stanford `Shared Computing`_ environment, once
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

    shell: str | None
    """
    The absolute path to the user's login shell.

    .. warning::
       Active accounts that use the default shell do not have this set.  The
       default shell was originally ``/bin/tcsh``, but changed to
       ``/bin/bash``.
    """

    @classmethod
    def _from_json(
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceLeland:
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
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServicePTS:
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

    This represents an account's AFS home volume.

    .. note::
       Just because someone has active AFS service, does not mean they actually
       have a home volume.  New Faculty and Staff members must `request an AFS
       home volume`_.

    .. tip::
       It is still possible to use AFS without a home volume, as long as you
       use a service (like FarmShare) that does not use AFS for home
       directories.

    .. _request an AFS home volume: https://uit.stanford.edu/service/afs/intro
    """

    homedirectory: str
    """
    The path to the account's home directory.

    .. note::
       This is used as the account's ``homeDirectory`` in LDAP.  As such, you
       will probably want to override it.

    .. note::
       This setting assumes that AFS is mounted at path ``/afs`` on a system.
       This is normally, but not always, the case.  This setting also assumes
       that your system has an up-to-date copy of the
       `CellServDB <https://docs.openafs.org/Reference/5/CellServDB.html>`_
       file, which should be the case if you are using a packaged OpenAFS
       client.
    """

    @classmethod
    def _from_json(
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceAFS:
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
        cls,
        source: dict[str, str | list[dict[str, str]]],
    ) -> AccountServiceDialin:
        # We don't have any settings.  Pull out common stuff and return.
        kwargs = cls._json_to_dict(source)
        return cls(**kwargs)
