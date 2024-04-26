{
    "name": "product_digi_sync",
    "summary": """
        Allows for syncing products to Digi using the @Fresh api""",
    "author": "Gedeelde Weelde",
    "license": "AGPL-3",
    "website": "https://www.yourcompany.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Sales/Point of Sale",
    "version": "16.0.0.0.1",
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/product_category_views.xml",
        "views/digi_client_views.xml",
        "views/digi_client_settings_view.xml",
        "views/barcode_rule.views.xml",
    ],
    # any module necessary for this one to work correctly
    "depends": ["product_food_fields", "product", "point_of_sale", "queue_job"],
    "installable": True,
}
