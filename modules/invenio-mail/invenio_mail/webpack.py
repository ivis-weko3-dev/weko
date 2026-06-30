from invenio_assets.webpack import WebpackThemeBundle

invenio_mail = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "invenio_mail_template_js": "./js/invenio_mail/mail_template.js"
            },
            dependencies={}
        )
    }
)
