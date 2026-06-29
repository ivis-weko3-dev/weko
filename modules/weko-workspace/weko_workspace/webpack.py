from invenio_assets.webpack import WebpackThemeBundle

weko_workspace = WebpackThemeBundle(
    __name__,
    "assets",
    default="bootstrap3",
    themes={
        "bootstrap3": dict(
            entry={
                "workspace_item_list_js": "./js/weko_workspace/WorkspaceItemList.js",
                "workspace_css": "./css/weko_workspace/WorkspaceBodyContents.css",
                "workspace_register_js": "./js/weko_workspace/workspace_register.js",
                "workspace_style_css": "./css/weko_workspace/style.css",
            },
            dependencies={},
        )
    }
)
