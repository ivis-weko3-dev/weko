
from invenio_oaiserver.receivers import (
    after_update_oai_set,
    after_delete_oai_set,
    after_insert_oai_set
)

def test_after_insert_oai_set(app,db,mocker):
    mocker.patch("invenio_oaiserver.receivers._new_percolator")
    class Target:
        @property
        def search_pattern(self):
            return "test_search_pattern"
        @property
        def spec(self):
            return "test_spec"
    after_insert_oai_set(None,None,Target())

# def after_update_oai_set(mapper, connection, target):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_receivers.py::test_after_update_oai_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_after_update_oai_set(app,db,mocker):
    class Target:
        @property
        def search_pattern(self):
            return "test_search_pattern"
        @property
        def spec(self):
            return "test_spec"
    mocker.patch("invenio_oaiserver.receivers._delete_percolator")
    mocker.patch("invenio_oaiserver.receivers._new_percolator")
    after_update_oai_set(None,None,Target())

# def after_delete_oai_set(mapper, connection, target):
# .tox/c1/bin/pytest --cov=invenio_oaiserver tests/test_receivers.py::test_after_delete_oai_set -vv -s --cov-branch --cov-report=term --basetemp=/code/modules/invenio-oaiserver/.tox/c1/tmp
def test_after_delete_oai_set(app,db,mocker):
    class Target:
        @property
        def search_pattern(self):
            return "test_search_pattern"
        @property
        def spec(self):
            return "test_spec"
    mocker.patch("invenio_oaiserver.receivers._delete_percolator")
    after_delete_oai_set(None,None,Target())
