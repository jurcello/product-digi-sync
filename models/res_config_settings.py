from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    digi_client_id = fields.Many2one(
        "product_digi_sync.digi_client", String="DigiClient to use"
    )
    digi_sync_products_enabled = fields.Boolean(
        String="Enable sending products to @Fresh"
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        configuration = self.env["ir.config_parameter"]
        digi_client_id = configuration.get_param("digi_client_id")
        res.update(
            digi_sync_products_enabled=configuration.get_param(
                "digi_sync_products_enabled", default=False
            ),
            digi_client_id=int(digi_client_id) if digi_client_id else False,
        )
        return res

    def set_values(self):
        configuration = self.env["ir.config_parameter"]
        configuration.set_param(
            "digi_sync_products_enabled", self.digi_sync_products_enabled
        )
        configuration.set_param("digi_client_id", self.digi_client_id.id)
        return super().set_values()
