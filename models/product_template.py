import re

from odoo import api, fields, models
from odoo.tools import get_barcode_check_digit


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plu_code = fields.Integer(string="Plu code", required=False)

    @api.depends("plu_code")
    def _compute_barcode(self):
        for record in self:
            if record.plu_code and record.categ_id.barcode_rule_id:
                pattern = record.categ_id.barcode_rule_id.pattern

                is_ean = record.categ_id.barcode_rule_id.encoding == "ean13"
                # Add barcode to vals
                record.barcode = record._prepare_barcode(
                    pattern, record.plu_code, is_ean
                )

    @staticmethod
    def _prepare_barcode(barcode_pattern, plu_code, is_ean13):
        # Converting the code to a padded string
        code_str = str(plu_code)
        code_length = barcode_pattern.count(".")
        padded_code = code_str.zfill(code_length)

        # Building the dot pattern for regex search
        dot_pattern = r"\.{" + str(code_length) + "}"

        # Replacing the specific number of dots with the padded code
        barcode = re.sub(dot_pattern, padded_code, barcode_pattern, count=1, flags=0)

        # Replacing whatever is inside the {} brackets with zeros
        repl_length = (
            len(re.findall(r"{.*}", barcode_pattern)[0]) - 2
        )  # subtract 2 for the {} brackets
        zeros = "0" * repl_length
        barcode = re.sub(r"{.*}", zeros, barcode, count=0, flags=0)
        if is_ean13:
            barcode_check_digit = get_barcode_check_digit(barcode + "0")
            barcode = f"{barcode}{barcode_check_digit}"

        return barcode

    def write(self, vals):
        result = super().write(vals)
        if self.plu_code:
            self.send_to_digi()
        self.send_image_to_digi()
        return result

    def send_to_digi(self):
        self.with_delay().send_to_digi_directly()

    def send_to_digi_directly(self):
        digi_client_id = int(
            self.env["ir.config_parameter"].get_param("digi_client_id")
        )
        client = self.env["product_digi_sync.digi_client"].browse(digi_client_id)
        if client.exists():
            client.send_product_to_digi(self)

    def send_image_to_digi(self):
        if not self.image_1920:
            return
        self.with_delay().send_image_to_digi_directly()

    def send_image_to_digi_directly(self):
        digi_client_id = int(
            self.env["ir.config_parameter"].get_param("digi_client_id")
        )
        client = self.env["product_digi_sync.digi_client"].browse(digi_client_id)
        if client.exists():
            client.send_product_image_to_digi(self)
