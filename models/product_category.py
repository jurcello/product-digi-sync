from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    barcode_rule_id = fields.Many2one("barcode.rule", string="Barcode Rule")
    external_digi_id = fields.Integer(
        string="External Digi identifier",
    )

    _sql_constraints = [
        (
            "external_digi_id",
            "unique(external_digi_id)",
            "External Digi identifier must be unique.",
        ),
    ]
