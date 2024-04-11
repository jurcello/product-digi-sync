import re

from odoo import fields, models, api
from odoo.tools import get_barcode_check_digit


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plu_code = fields.Integer(string="Plu code", required=False)
    barcode_rule_id = fields.Many2one("barcode.rule", string="Barcode Rule")

    @api.depends("plu_code")
    def _compute_barcode(self):
        if self.plu_code and self.barcode_rule_id:
            pattern = self.barcode_rule_id.pattern
            # Ensure the plu_code is at least 5 characters long, padding with leading zeros if necessary

            is_ean = self.barcode_rule_id.encoding == "ean13"
            # Add barcode to vals
            self.barcode = self._prepare_barcode(pattern, self.plu_code, is_ean)

    def _prepare_barcode(self, barcode_pattern, plu_code, is_ean13):
        # Converting the code to a padded string
        code_str = str(plu_code)
        code_length = barcode_pattern.count(".")
        padded_code = code_str.zfill(code_length)

        # Building the dot pattern for regex search
        dot_pattern = r"\.{" + str(code_length) + "}"

        # Replacing the specific number of dots with the padded code
        barcode = re.sub(dot_pattern, padded_code, barcode_pattern, 1)

        # Replacing whatever is inside the {} brackets with zeros
        repl_length = (
            len(re.findall(r"{.*}", barcode_pattern)[0]) - 2
        )  # subtract 2 for the {} brackets
        zeros = "0" * repl_length
        barcode = re.sub(r"{.*}", zeros, barcode)
        if is_ean13:
            barcode_check_digit = get_barcode_check_digit(barcode + "0")
            barcode = f"{barcode}{barcode_check_digit}"

        return barcode
