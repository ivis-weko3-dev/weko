import os
import json
import copy
import pytest
import unittest
from mock import patch, MagicMock, Mock
from flask import Flask
from flask_login import current_user
from flask_babel import Babel

from weko_search_ui.ext import WekoSearchUI, WekoSearchREST


# class WekoSearchUI
def test_WekoSearchUI(instance_path):
    app = Flask('testapp', instance_path=instance_path)
    test = WekoSearchUI(app)
    assert test

# def test_WekoSearchUI_2(i18n_app, app):
#     app.config.pop("INDEX_IMG")
#     test = WekoSearchUI(app)
#     assert test


# class WekoSearchREST
def test_WekoSearchREST(i18n_app):
    test = WekoSearchREST(i18n_app)

    assert test