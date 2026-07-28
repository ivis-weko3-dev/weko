
import weko_index_tree.config as weko_index_tree_config
from weko_index_tree.ext import WekoIndexTree, WekoIndexTreeREST

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp

# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::test_WekoIndexTree -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
class TestWekoIndexTree:

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::test_WekoIndexTree_with_base_edit_template -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_init_app_with_base_edit_template(self, app, db):
        app.config['BASE_EDIT_TEMPLATE'] = 'custom/base.html'
        ext = WekoIndexTree(app)

        assert 'weko_index_tree' in app.blueprints
        assert app.extensions['weko-index-tree'] is ext
        assert app.config['WEKO_INDEX_TREE_BASE_TEMPLATE'] == 'custom/base.html'


    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::test_WekoIndexTree_without_base_edit_template -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_init_app_without_base_edit_template(self, app, db):
        ext = WekoIndexTree(app)

        assert 'weko_index_tree' in app.blueprints
        assert app.extensions['weko-index-tree'] is ext
        # When BASE_EDIT_TEMPLATE is absent, the default value from config.py is used
        assert app.config['WEKO_INDEX_TREE_BASE_TEMPLATE'] == \
            weko_index_tree_config.WEKO_INDEX_TREE_BASE_TEMPLATE

    def test_init_app_does_not_overwrite_existing_config(self, app, db):
        # Verify that an already-set value is not overwritten, since setdefault is used
        app.config['WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER'] = 999
        WekoIndexTree(app)
        assert app.config['WEKO_INDEX_TREE_DEFAULT_DISPLAY_NUMBER'] == 999


# .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::TestWekoIndexTreeREST -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
class TestWekoIndexTreeREST:

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::TestWekoIndexTreeREST::test_init_app -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_init_app(self, app, db):
        ext = WekoIndexTreeREST(app)
        assert 'weko_index_tree_rest' in app.blueprints
        assert app.extensions['weko-index-tree-rest'] is ext

    # .tox/c1/bin/pytest --cov=weko_index_tree tests/test_ext.py::TestWekoIndexTreeREST::test_init_app_no_app -v -s -vv --cov-branch --cov-report=term --cov-config=tox.ini --basetemp=/code/modules/weko-index-tree/.tox/c1/tmp
    def test_init_app_no_app(self, app, db):
        # When app=None, nothing is initialized
        ext = WekoIndexTreeREST()
        assert ext is not None
