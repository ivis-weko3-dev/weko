from invenio_assets.webpack import WebpackThemeBundle

weko_notifications = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "notifications_settings_css": "./css/weko_notifications/notifications.settings.css",
                "notifications_settings_js": "./js/weko_notifications/notifications.settings.js",
                "notifications_sw_js": "./js/weko_notifications/sw.js",
            },
            dependencies={
                "react": "~15.6.1",
                "react-dom": "~15.6.1",
                "jquery": "~2.1.3"
            }
        )
    }
)
