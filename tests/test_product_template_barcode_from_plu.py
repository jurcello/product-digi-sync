from odoo.tests import TransactionCase, tagged


class ProductTemplateBarcodeFromPluTestCase(TransactionCase):
    @tagged("post_install", "-at_install")
    def test_setting_plu_sets_updates_barcode(self):
        barcode_rule = self.env["barcode.rule"].search(
            [("name", "=", "Price Barcodes 2 Decimals")]
        )

        product_category = self.env["product.category"].create(
            {
                "name": "Test Product Category",
                "barcode_rule_id": barcode_rule.id,
            }
        )
        # Test case code here
        product_template = self.env["product.template"].create(
            {"name": "dummy_name", "plu_code": 100, "categ_id": product_category.id}
        )

        self.assertEqual(product_template.barcode, "2300100000008")
