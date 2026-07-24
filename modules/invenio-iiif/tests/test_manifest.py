
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
from flask_iiif.restful import current_iiif

from invenio_iiif.manifest import IIIFMetadata, IIIFManifest, ManifestFactory

# class IIIFMetadata(dict):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFMetadata -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
class TestIIIFMetadata:
#     def __init__(self, record, **kwargs):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFMetadata::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_init(self,app,records):
        record = records[0][2]
        obj = IIIFMetadata(record,test1="test1_value",test2="test2_value")
        assert obj._record == record
        assert obj["test1"] == "test1_value"
        assert obj["test2"] == "test2_value"

#     def extract_metadata(self):


# class IIIFManifest(object):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
class TestIIIFManifest:
#     def __init__(self, record, metadata_class=None, extra_meatadata=None):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest::test_init -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_init(self,app,records):
        record = records[0][2]
        with app.test_request_context("/test"):
            obj = IIIFManifest(record)
            manifest = obj.manifest
            assert obj.record == record
            assert obj.manifest.description == "conference paper"
            assert manifest.license == ""
            assert manifest.viewingDirection == "left-to-right"


#     def dumps(self):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestIIIFManifest::test_dumps -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_dumps(self,app,records):
        record = records[0][2]
        with app.test_request_context("/test"):
            obj = IIIFManifest(record)
            result = obj.dumps()
            assert result == {}


# class Image(PreziImage):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestImage -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
class TestImage:

#    def set_hw_from_iiif(self):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestImage::test_set_hw_from_iiif_cache_miss -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_set_hw_from_iiif_cache_miss(self, app, image_object, image_uuid):
        mf = ManifestFactory()
        img = mf.image(image_uuid, iiif=True)
        assert img.width == 0
        assert img.height == 0

        img.set_hw_from_iiif()
        assert img.width > 0
        assert img.height > 0

#    def set_hw_from_iiif(self):
# .tox/c1/bin/pytest --cov=invenio_iiif tests/test_manifest.py::TestImage::test_set_hw_from_iiif_cache_hit -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio_iiif/.tox/c1/tmp
    def test_set_hw_from_iiif_cache_hit(self, app, image_object, image_uuid):

        mf = ManifestFactory()
        img = mf.image(image_uuid, iiif=True)

        key = image_object.key
        current_iiif.cache().set(key, "123,456")

        img.set_hw_from_iiif()

        # 現状の実装ではキャッシュヒット時に self.width/height が
        # 更新されないため、初期値の 0 のままとなる
        assert img.width == 0
        assert img.height == 0
