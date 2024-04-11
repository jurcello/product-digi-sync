from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    barcode_rule_id = fields.Many2one("barcode.rule", string="Barcode Rule")
