import pytest
from mock import patch, MagicMock

from weko_records.serializers.dc import DcWekoBaseExtension, DcWekoEntryExtension

# .tox/c1/bin/pytest --cov=weko_records tests/test_serializers_dc.py::test_dc_creator -v -s -vv --cov-branch --cov-report=term --cov-report=html --cov-config=tox.ini --basetemp=/code/modules/weko-records/.tox/c1/tmp
# class DcWekoBaseExtension(JSONSerializer): 
# def dc_creator
def test_dc_creator(app):
    test = DcWekoBaseExtension()
    # creator: None, lang: None
    assert test.dc_creator() is None

    # creator: str, lang: None
    result = test.dc_creator(creator="creator1")
    assert result == ["creator1"]

    # creator: list, lang: None
    result = test.dc_creator(creator=["creator2", "creator3"], replace=True)
    assert result == ["creator2", "creator3"]

    # creator: str, lang: str
    result = test.dc_creator(creator="creator4", lang="ja", replace=True)
    assert result == ["creator4"]
    assert test._dcelem_creator_lang == ["ja"]

    # creator: str, lang: list
    result = test.dc_creator(creator="creator5", lang=["en"], replace=True)
    assert result == ["creator5"]
    assert test._dcelem_creator_lang == ["en"]

    # creator: list, lang: list, replace=False（既存値に追加されることを確認）
    result = test.dc_creator(creator=["creator6", "creator7"], lang=["de", "it"], replace=False)
    assert result == ["creator5", "creator6", "creator7"]
    assert test._dcelem_creator_lang == ["en", "de", "it"]


# class DcWekoEntryExtension(JSONSerializer): 
# def extend_atom
def test_extend_atom(app):
    test = DcWekoEntryExtension()
    def _extend_xml(item):
        return item

    test._extend_xml = _extend_xml
    entry = "entry"

    assert test.extend_atom(
        entry=entry
    ) != None


# def extend_jpcoar
def test_extend_jpcoar(app):
    test = DcWekoEntryExtension()
    def _extend_xml(item):
        return item

    test._extend_xml = _extend_xml
    item = "item"

    assert test.extend_jpcoar(
        item=item
    ) != None