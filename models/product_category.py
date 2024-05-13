from odoo import api, fields, models


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

    def write(self, vals):
        for record in self:
            if record.external_digi_id:
                record.send_to_digi()
        result = super().write(vals)
        return result

    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.external_digi_id:
            record.send_to_digi()

        return record

    def send_to_digi(self):
        self.with_delay().send_to_digi_directly()

    def send_to_digi_directly(self):
        digi_client_id = int(
            self.env["ir.config_parameter"].get_param("digi_client_id")
        )
        client = self.env["product_digi_sync.digi_client"].browse(digi_client_id)
        if client.exists():
            client.send_category_to_digi(self)
