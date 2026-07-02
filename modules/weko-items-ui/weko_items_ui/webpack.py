from invenio_assets.webpack import WebpackThemeBundle

weko_items_ui = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "items_ui_css_indextree_style": "./css/weko_items_ui/indextree_style.css",
                "items_ui_css_items_author_search": "./css/weko_items_ui/styles.items.authorSearch.bundle.css",
                "items_ui_js_app": "./js/weko_items_ui/app.js",
                "items_ui_js_upload": "./js/weko_items_ui/upload.js",
                "items_ui_js_feedback_maillist": "./js/weko_items_ui/feedback_maillist.js",
                "items_ui_css_feedback_maillist": "./css/weko_items_ui/feedback.mail.css",
                "items_ui_js_request_maillist": "./js/weko_items_ui/request_maillist.js",
                "items_ui_no_file_approval_js": "./js/weko_items_ui/no_file_approval.js",
                "items_ui_oapolicy_js": "./js/weko_items_ui/oapolicy.js",
            },
            dependencies={
                'angular': "~1.4.9",
                "bootstrap": "~3.3.7",
                "jquery": "~3.2.1",
                'lodash': '~3.10.1',
                "react": "~15.6.1",
                "react-bootstrap": "~0.33.1",
                "react-dom": "~15.6.1",
            }
        )
    }
)
