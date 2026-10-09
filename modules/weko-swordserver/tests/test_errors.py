# -*- coding: utf-8 -*-
"""Tests for weko_swordserver.errors (W2026-64 step 1)."""

import os

import pytest
from babel.messages.pofile import read_po
from flask import Flask
from flask_babelex import Babel

import weko_swordserver
from weko_swordserver import errors
from weko_swordserver.errors import (
    ErrorSpec, ErrorType, WekoSwordserverException,
    SwordClientException, SwordConditionException, SwordServerException,
    AuthorizationException, InputHeaderException, ContentFormatException,
    DataValidationException, ResourceStateException, ConcurrencyException,
    RateLimitException, IncompleteProcessException, InternalProcessException,
    UnexpectedException, _default_catalog)

# class -> (parent, code band prefix)
CLASSES = {
    AuthorizationException: (SwordClientException, "12"),
    InputHeaderException: (SwordClientException, "13"),
    ContentFormatException: (SwordClientException, "14"),
    DataValidationException: (SwordClientException, "15"),
    ResourceStateException: (SwordConditionException, "21"),
    ConcurrencyException: (SwordConditionException, "22"),
    RateLimitException: (SwordConditionException, "23"),
    IncompleteProcessException: (SwordConditionException, "24"),
    InternalProcessException: (SwordServerException, "31"),
    UnexpectedException: (SwordServerException, "32"),
}
TRANSLATIONS = os.path.join(os.path.dirname(weko_swordserver.__file__), "translations")


def all_specs():
    """Return [(cls, attr_name, spec)] for every ErrorSpec."""
    return [(c, n, v) for c in CLASSES for n, v in vars(c).items()
            if isinstance(v, ErrorSpec)]


def msgids(path):
    with open(path, "rb") as f:
        return {m.id: m.string for m in read_po(f) if m.id}


# (class, attr, params, code, ErrorType, http, message)
REPRESENTATIVES = [
    (IncompleteProcessException, "UPDATE_PENDING_COMPLETION",
     {"recid": 3, "url": "u"}, "2402", ErrorType.BadRequest, 400,
     "Update of item 3 is pending completion. Please open the following URL "
     "to continue with the remaining operations: u."),
    (ConcurrencyException, "ITEM_LOCKED", {"recid": 7}, "2201",
     ErrorType.Conflict, 409, "Item 7 will be edited by another process."),
    (UnexpectedException, "INTERNAL_SERVER_ERROR", {}, "3201",
     ErrorType.NotImplemented, 501, "Internal Server Error"),
]


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace

# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_spec_factory -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_spec_factory():
    for cls, name, params, code, etype, http, message in REPRESENTATIVES:
        spec = vars(cls)[name]
        assert isinstance(spec, ErrorSpec) and spec.key == name
        e = getattr(cls, name)(**params)
        assert isinstance(e, cls)
        assert (e.error_code, e.errorType, e.errorType.code) == (code, etype, http)
        assert e.message == message == str(e)


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_class_hierarchy -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_class_hierarchy():
    for cls, (parent, _) in CLASSES.items():
        assert issubclass(cls, parent)
        assert issubclass(parent, WekoSwordserverException)


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_legacy_form -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_legacy_form():
    e = WekoSwordserverException("m", ErrorType.BadRequest)
    assert (e.error_code, e.message, str(e), e.errorType) == (
        None, "m", "m", ErrorType.BadRequest)
    assert WekoSwordserverException("m").errorType == ErrorType.ServerError


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_missing_placeholder_raises_key_error -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_missing_placeholder_raises_key_error():
    with pytest.raises(KeyError):
        ResourceStateException.ITEM_NOT_FOUND()


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_merge -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_merge():
    def mk(d):
        return DataValidationException.ITEM_CHECK_ERROR(detail=d)
    a = mk("a")
    r = WekoSwordserverException.merge([a, mk("b")])
    assert r is a and r.error_code == "1501"
    assert r.message == "Item check error: a; Item check error: b"
    assert WekoSwordserverException.merge([mk("c"), mk("d")], sep="|").message \
        == "Item check error: c|Item check error: d"


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_spec_name_is_msgid_and_code_band_matches_class -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_spec_name_is_msgid_and_code_band_matches_class():
    specs = all_specs()
    assert specs
    for cls, name, spec in specs:
        assert spec.key == name
        assert len(spec.code) == 4 and spec.code.isdigit(), name
        assert spec.code.startswith(CLASSES[cls][1]), name


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_codes_unique -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_codes_unique():
    codes = [s.code for _, _, s in all_specs()]
    assert len(codes) == len(set(codes))


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_catalog_msgids_match_specs -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_catalog_msgids_match_specs():
    expected = {n for _, n, _ in all_specs()}
    assert set(msgids(os.path.join(TRANSLATIONS, "messages.pot"))) == expected
    en = msgids(os.path.join(TRANSLATIONS, "en", "LC_MESSAGES", "messages.po"))
    assert set(en) == expected


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_en_msgstr_not_empty_and_mo_in_sync -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_en_msgstr_not_empty_and_mo_in_sync():
    en = msgids(os.path.join(TRANSLATIONS, "en", "LC_MESSAGES", "messages.po"))
    cat = _default_catalog()
    for k, v in en.items():
        assert v.strip(), k
        assert cat.gettext(k) == v, k


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_fallback_to_english_for_locale_without_catalog -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_fallback_to_english_for_locale_without_catalog():
    app = Flask(__name__)
    Babel(app, default_locale="fr")
    with app.test_request_context("/"):
        e = ResourceStateException.ITEM_NOT_FOUND(recid=5)
        assert e.message == "Item not found. (recid=5)"


# .tox/c1/bin/pytest --cov=weko_swordserver tests/test_errors.py::test_translated_text_is_used_without_fallback -v -vv -s --cov-branch --cov-report=term --cov-report=html --basetemp=/code/modules/weko-swordserver/.tox/c1/tmp --full-trace
def test_translated_text_is_used_without_fallback():
    class Dummy(SwordClientException):
        X = ErrorSpec("1999", "translated {a}", ErrorType.BadRequest)
    e = Dummy.X(a=1)
    assert e.message == "translated 1"
    assert e.error_code == "1999"
