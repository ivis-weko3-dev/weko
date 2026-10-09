# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 National Institute of Informatics.
#
# WEKO-SWORDServer is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Useful errors in weko-swordserver."""

import functools
import os
from enum import Enum

from babel.support import Translations
from flask_babelex import lazy_gettext as _

ERROR_CODE_PREFIX = "WEKO_SWORDSERVER_E_"


class ErrorType(Enum):
    # Swordv3 ErrorType
    BadRequest                      = ("BadRequest",                    400, "BadRequest")
    ByReferenceFileSizeExceeded     = ("ByReferenceFileSizeExceeded",   400, "BadRequest")
    ContentMalformed                = ("ContentMalformed",              400, "BadRequest")
    InvalidSegmentSize              = ("InvalidSegmentSize",            400, "BadRequest")
    MaxAssembledSizeExceeded        = ("MaxAssembledSizeExceeded",      400, "BadRequest")
    SegmentLimitExceeded            = ("SegmentLimitExceeded",          400, "BadRequest")
    UnexpectedSegment               = ("UnexpectedSegment",             400, "BadRequest")
    AuthenticationRequired          = ("AuthenticationRequired",        401, "Unauthorized")
    AuthenticationFailed            = ("AuthenticationFailed",          403, "Forbidden")
    Forbidden                       = ("Forbidden",                     403, "Forbidden")
    MethodNotAllowed	            = ("MethodNotAllowed",              405, "MethodNotAllowed")
    SegmentedUploadTimedOut         = ("SegmentedUploadTimedOut",       410, "MethodNotAllowed")
    ByReferenceNotAllowed           = ("ByReferenceNotAllowed",         412, "PreconditionFailed")
    DigestMismatch                  = ("DigestMismatch",                412, "PreconditionFailed")
    ETagNotMatched                  = ("ETagNotMatched",                412, "PreconditionFailed")
    ETagRequired                    = ("ETagRequired",                  412, "PreconditionFailed")
    OnBehalfOfNotAllowed            = ("OnBehalfOfNotAllowed",          412, "PreconditionFailed")
    MaxUploadSizeExceeded           = ("MaxUploadSizeExceeded",         413, "PayloadTooLarge")
    ContentTypeNotAcceptable        = ("ContentTypeNotAcceptable",      415, "UnsupportedMediaType")
    FormatHeaderMismatch            = ("FormatHeaderMismatch",          415, "UnsupportedMediaType")
    MetadataFormatNotAcceptable     = ("MetadataFormatNotAcceptable",   415, "UnsupportedMediaType")
    PackagingFormatNotAcceptable    = ("PackagingFormatNotAcceptable",  415, "UnsupportedMediaType")

    # Addlitional ErrorType
    NotFound                        = ("NotFound",                      404, "NotFound")
    Conflict                        = ("Conflict",                      409, "Conflict")
    TooManyRequests                 = ("TooManyRequests",               429, "TooManyRequests")
    ServerError                     = ("ServerError",                   500, "InternalServerError")
    NotImplemented                  = ("NotImplemented",                501, "NotImplemented")
    ServiceUnavailable              = ("ServiceUnavailable",            503, "ServiceUnavailable")

    def __init__(self, type, code, httpName):
        self.type = type
        self.code = code
        self.httpName = httpName


class ErrorSpec:
    """Per-message spec. Use as ``Cls.SPEC(**params)``."""

    def __init__(self, code, msgid, error_type):
        """Initialize ErrorSpec."""
        self.code, self.msgid, self.error_type = code, msgid, error_type

    def __set_name__(self, owner, name):
        """Keep the attribute name (= msgid) for the fallback check."""
        self.key = name

    def __get__(self, obj, owner):
        """Return a factory of the exception for this spec."""
        return lambda **params: owner(spec=self, **params)


@functools.lru_cache(maxsize=None)
def _default_catalog():
    """Load the ``en`` catalog bundled in the package."""
    return Translations.load(
        os.path.join(os.path.dirname(__file__), "translations"), ["en"])


class WekoSwordserverException(Exception):
    """Base exception of weko-swordserver."""

    errorType = ErrorType.ServerError   # default for legacy form (no spec)
    error_code = None                   # legacy form has no code
    message = ""

    def __init__(self, message=None, errorType=None, spec=None, **params):
        """Initialize WekoSwordserverException."""
        if spec is not None:
            self.error_code = spec.code
            text = str(spec.msgid)  # evaluate the translation at raise time
            if text == spec.key:  # no catalog for the locale: use en
                text = _default_catalog().gettext(spec.key)
            message = text.format(**params)
            errorType = spec.error_type
        self.message = message
        self.errorType = errorType or type(self).errorType
        super().__init__(message)

    @staticmethod
    def merge(errors, sep="; "):
        """Merge errors of the same spec into the first one."""
        first = errors[0]
        first.message = sep.join(e.message for e in errors)
        first.args = (first.message,)
        return first


class SwordClientException(WekoSwordserverException):
    """Client-caused errors (1xxx)."""


class AuthorizationException(SwordClientException):
    """12xx errors."""

    ACTIVITY_SCOPE_INSUFFICIENT = ErrorSpec("1201", _("ACTIVITY_SCOPE_INSUFFICIENT"), ErrorType.Forbidden)
    ON_BEHALF_OF_NOT_ALLOWED = ErrorSpec("1202", _("ON_BEHALF_OF_NOT_ALLOWED"), ErrorType.OnBehalfOfNotAllowed)
    ON_BEHALF_OF_USER_NOT_FOUND = ErrorSpec("1203", _("ON_BEHALF_OF_USER_NOT_FOUND"), ErrorType.BadRequest)
    ON_BEHALF_OF_USER_ROLE_FORBIDDEN = ErrorSpec("1204", _("ON_BEHALF_OF_USER_ROLE_FORBIDDEN"), ErrorType.Forbidden)


class InputHeaderException(SwordClientException):
    """13xx errors."""

    FILE_PART_MISSING = ErrorSpec("1301", _("FILE_PART_MISSING"), ErrorType.ContentMalformed)
    FILE_NOT_SELECTED = ErrorSpec("1302", _("FILE_NOT_SELECTED"), ErrorType.ContentMalformed)
    FILENAME_UNRESOLVABLE = ErrorSpec("1303", _("FILENAME_UNRESOLVABLE"), ErrorType.BadRequest)
    FILE_NOT_FOUND_IN_BODY = ErrorSpec("1304", _("FILE_NOT_FOUND_IN_BODY"), ErrorType.BadRequest)
    UPLOAD_SIZE_EXCEEDED = ErrorSpec("1305", _("UPLOAD_SIZE_EXCEEDED"), ErrorType.MaxUploadSizeExceeded)
    DIGEST_MISMATCH = ErrorSpec("1306", _("DIGEST_MISMATCH"), ErrorType.DigestMismatch)


class ContentFormatException(SwordClientException):
    """14xx errors."""

    CONTENT_TYPE_NOT_ACCEPTABLE = ErrorSpec("1401", _("CONTENT_TYPE_NOT_ACCEPTABLE"), ErrorType.ContentTypeNotAcceptable)
    PACKAGING_NOT_ACCEPTABLE = ErrorSpec("1402", _("PACKAGING_NOT_ACCEPTABLE"), ErrorType.PackagingFormatNotAcceptable)
    PACKAGING_REQUIRED = ErrorSpec("1403", _("PACKAGING_REQUIRED"), ErrorType.PackagingFormatNotAcceptable)
    SWORDBAGIT_METADATA_MISSING = ErrorSpec("1404", _("SWORDBAGIT_METADATA_MISSING"), ErrorType.MetadataFormatNotAcceptable)
    SIMPLEZIP_UNEXPECTED_SWORD_JSON = ErrorSpec("1405", _("SIMPLEZIP_UNEXPECTED_SWORD_JSON"), ErrorType.MetadataFormatNotAcceptable)
    ROCRATE_METADATA_MISSING = ErrorSpec("1406", _("ROCRATE_METADATA_MISSING"), ErrorType.MetadataFormatNotAcceptable)
    SIMPLEZIP_METADATA_FILE_MISSING = ErrorSpec("1407", _("SIMPLEZIP_METADATA_FILE_MISSING"), ErrorType.ContentMalformed)
    PACKAGING_FORMAT_NOT_ACCEPTABLE = ErrorSpec("1408", _("PACKAGING_FORMAT_NOT_ACCEPTABLE"), ErrorType.PackagingFormatNotAcceptable)
    METADATA_IMPORT_DISABLED = ErrorSpec("1409", _("METADATA_IMPORT_DISABLED"), ErrorType.MetadataFormatNotAcceptable)
    XML_DIRECT_REGISTRATION_NOT_ALLOWED = ErrorSpec("1410", _("XML_DIRECT_REGISTRATION_NOT_ALLOWED"), ErrorType.MetadataFormatNotAcceptable)
    UNSUPPORTED_FILE_FORMAT = ErrorSpec("1411", _("UNSUPPORTED_FILE_FORMAT"), ErrorType.MetadataFormatNotAcceptable)


class DataValidationException(SwordClientException):
    """15xx errors."""

    ITEM_CHECK_ERROR = ErrorSpec("1501", _("ITEM_CHECK_ERROR"), ErrorType.ContentMalformed)
    ITEM_ALREADY_REGISTERED = ErrorSpec("1502", _("ITEM_ALREADY_REGISTERED"), ErrorType.BadRequest)
    ITEM_DUPLICATE_SUSPECTED = ErrorSpec("1503", _("ITEM_DUPLICATE_SUSPECTED"), ErrorType.BadRequest)
    MULTIPLE_ITEMS_IN_PUT = ErrorSpec("1504", _("MULTIPLE_ITEMS_IN_PUT"), ErrorType.ContentMalformed)
    ITEM_NOT_REGISTERED_FOR_PUT = ErrorSpec("1505", _("ITEM_NOT_REGISTERED_FOR_PUT"), ErrorType.BadRequest)
    ITEM_ID_MISMATCH = ErrorSpec("1506", _("ITEM_ID_MISMATCH"), ErrorType.BadRequest)


class SwordConditionException(WekoSwordserverException):
    """Boundary/operational condition errors (2xxx)."""


class ResourceStateException(SwordConditionException):
    """21xx errors."""

    ITEM_NOT_FOUND = ErrorSpec("2101", _("ITEM_NOT_FOUND"), ErrorType.NotFound)
    RECORD_NOT_FOUND = ErrorSpec("2102", _("RECORD_NOT_FOUND"), ErrorType.NotFound)
    SWORD_CLIENT_NOT_CONFIGURED = ErrorSpec("2103", _("SWORD_CLIENT_NOT_CONFIGURED"), ErrorType.BadRequest)
    WORKFLOW_NOT_FOUND = ErrorSpec("2104", _("WORKFLOW_NOT_FOUND"), ErrorType.BadRequest)
    WORKFLOW_NOT_FOR_REGISTRATION = ErrorSpec("2105", _("WORKFLOW_NOT_FOR_REGISTRATION"), ErrorType.BadRequest)
    ITEM_HAS_DOI = ErrorSpec("2106", _("ITEM_HAS_DOI"), ErrorType.BadRequest)


class ConcurrencyException(SwordConditionException):
    """22xx errors."""

    ITEM_LOCKED = ErrorSpec("2201", _("ITEM_LOCKED"), ErrorType.Conflict)
    ITEM_IMPORT_IN_PROGRESS = ErrorSpec("2202", _("ITEM_IMPORT_IN_PROGRESS"), ErrorType.Conflict)
    ITEM_BEING_EDITED = ErrorSpec("2203", _("ITEM_BEING_EDITED"), ErrorType.Conflict)


class RateLimitException(SwordConditionException):
    """23xx errors."""

    RATE_LIMIT_EXCEEDED = ErrorSpec("2301", _("RATE_LIMIT_EXCEEDED"), ErrorType.TooManyRequests)


class IncompleteProcessException(SwordConditionException):
    """24xx errors."""

    REGISTRATION_PENDING_COMPLETION = ErrorSpec("2401", _("REGISTRATION_PENDING_COMPLETION"), ErrorType.BadRequest)
    UPDATE_PENDING_COMPLETION = ErrorSpec("2402", _("UPDATE_PENDING_COMPLETION"), ErrorType.BadRequest)


class SwordServerException(WekoSwordserverException):
    """Server-caused errors (3xxx)."""


class InternalProcessException(SwordServerException):
    """31xx errors."""

    DB_ACCESS_FAILURE = ErrorSpec("3101", _("DB_ACCESS_FAILURE"), ErrorType.ServiceUnavailable)
    INVALID_REGISTRATION_TYPE = ErrorSpec("3102", _("INVALID_REGISTRATION_TYPE"), ErrorType.ServerError)
    INVALID_REGISTER_FORMAT = ErrorSpec("3103", _("INVALID_REGISTER_FORMAT"), ErrorType.ServerError)
    IMPORT_FAILURE = ErrorSpec("3104", _("IMPORT_FAILURE"), ErrorType.ServerError)
    UPDATE_FAILURE = ErrorSpec("3105", _("UPDATE_FAILURE"), ErrorType.ServerError)
    DELETE_FAILURE = ErrorSpec("3106", _("DELETE_FAILURE"), ErrorType.ServerError)
    ACTIVITY_NOT_FOUND_AFTER_CREATE = ErrorSpec("3107", _("ACTIVITY_NOT_FOUND_AFTER_CREATE"), ErrorType.NotImplemented)
    DATABASE_UNAVAILABLE = ErrorSpec("3108", _("DATABASE_UNAVAILABLE"), ErrorType.ServiceUnavailable)
    REDIS_UNAVAILABLE = ErrorSpec("3109", _("REDIS_UNAVAILABLE"), ErrorType.ServiceUnavailable)
    SEARCH_ENGINE_UNAVAILABLE = ErrorSpec("3110", _("SEARCH_ENGINE_UNAVAILABLE"), ErrorType.ServiceUnavailable)


class UnexpectedException(SwordServerException):
    """32xx errors."""

    INTERNAL_SERVER_ERROR = ErrorSpec("3201", _("INTERNAL_SERVER_ERROR"), ErrorType.NotImplemented)
    UNEXPECTED_DURING_DELETION = ErrorSpec("3202", _("UNEXPECTED_DURING_DELETION"), ErrorType.NotImplemented)
