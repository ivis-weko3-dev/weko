from invenio_assets.webpack import WebpackThemeBundle

weko_logging = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "logging_export_css": "./css/weko_logging/export.less",
                "logging_export_js": "./js/weko_logging/export.js",
            },
            dependencies={
                "react": "~15.6.1",
                "react-dom": "~15.6.1",
                "jquery": "~2.1.3"
            }
        )
    }
)
