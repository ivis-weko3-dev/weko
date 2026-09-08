from invenio_assets.webpack import WebpackThemeBundle

invenio_communities = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "communities_js_js": "./js/invenio_communities/main.js",
                "communities_css_css": "./scss/invenio_communities/communities.scss",
                "communities_css_css_tree": "./scss/invenio_communities/styles.community.bundle.css",
                "communities_css_css_tree_display": "./scss/invenio_communities/styles.bundle.css",
                "communities_css_trumbowyg": "./scss/invenio_communities/css.css",
                "communities_js_trumbowyg": "./js/invenio_communities/js.js",
                "communities_js_app": "./js/invenio_communities/app.js",
                "communities_css_extra_fields": "./scss/invenio_communities/extra_fields.css",
                "communities_js_communities_list": "./js/invenio_communities/communities_list.js",
            },
            dependencies={
                "angular": "~1.4.9",
                "ckeditor": "~4.5.8",
                "jquery": "~3.2.1",
                "trumbowyg": "~2.25.1"
            }
        )
    }
)
