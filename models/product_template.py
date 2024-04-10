from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plu_code = fields.Integer(string="Plu code", required=False)
