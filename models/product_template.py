import re

from odoo import api, fields, models
from odoo.tools import get_barcode_check_digit


class ProductTemplate(models.Model):
    _inherit = "product.template"

    plu_code = fields.Integer(string="Plu code", required=False)
    barcode_rule_id = fields.Many2one("barcode.rule", string="Barcode Rule")

    @api.depends("plu_code")
    def _compute_barcode(self):
        if self.plu_code and self.categ_id.barcode_rule_id:
            pattern = self.categ_id.barcode_rule_id.pattern

            is_ean = self.categ_id.barcode_rule_id.encoding == "ean13"
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
