from odoo import fields, models


class BarcodeRule(models.Model):
    _inherit = "barcode.rule"

    digi_barcode_type_id = fields.Integer(string="Barcode Type ID in @Fresh", default=0)
