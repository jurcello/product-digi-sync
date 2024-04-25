from unittest.mock import patch

from odoo.tests import TransactionCase

from odoo.addons.base.models.ir_config_parameter import IrConfigParameter
from odoo.addons.product_digi_sync.models.digi_client import DigiClient


class ProductCategoryTestCase(TransactionCase):
    def test_it_doesn_send_the_category_to_digi_after_save_when_external_id_not_set(
        self
    ):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )

        patch.object(IrConfigParameter, "get_param", digi_client.id)

        with patch.object(
            DigiClient, "send_category_to_digi"
        ) as mock_send_category_to_digi:
            category = self.env["product.category"].create(
                {
                    "name": "Test Category",
                }
            )
            category.write(
                {
                    "name": "Test Category altered",
                }
            )

            self.assertEqual(mock_send_category_to_digi.call_count, 0)

    def test_is_sends_the_category_to_digi_when_external_id_is_set(self):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )

        patch.object(IrConfigParameter, "get_param", digi_client.id)

        with patch.object(
            DigiClient, "send_category_to_digi"
        ) as mock_send_category_to_digi:
            category = self.env["product.category"].create(
                {
                    "name": "Test Category",
                    "external_digi_id": 1145,
                }
            )
            category.write(
                {
                    "name": "Test Category altered",
                }
            )

            self.assertEqual(mock_send_category_to_digi.call_args[0][0], category)
