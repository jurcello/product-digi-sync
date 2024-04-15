import base64
import io
from unittest.mock import Mock, patch

from PIL import Image

from odoo.tests import TransactionCase

from odoo.addons.base.models.ir_config_parameter import IrConfigParameter
from odoo.addons.product_digi_sync.models.digi_client import DigiClient


class ProductTemplateTestCase(TransactionCase):
    def test_it_sends_the_product_to_digi_when_plu_code_is_set(self):
        product = self.env["product.template"].create(
            {"name": "Test Product Template", "plu_code": 405}
        )

        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )

        patch.object(IrConfigParameter, "get_param", digi_client.id)
        mock_send_product_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_to_digi", mock_send_product_to_digi
        ).start()
        patch.object(DigiClient, "send_product_image_to_digi", Mock()).start()

        product.write(
            {
                "name": "Test Product Template",
            }
        )

        self.assertEqual(mock_send_product_to_digi.call_args[0][0], product)

    def test_it_sends_the_product_image_to_digi_when_the_image_is_set(self):
        digi_client = self.env["product_digi_sync.digi_client"].create(
            {
                "name": "Test Digi Client",
                "username": "user",
                "password": "<PASSWORD>",
            }
        )

        patch.object(IrConfigParameter, "get_param", digi_client.id)
        mock_send_product_image_to_digi = Mock()
        patch.object(
            DigiClient, "send_product_image_to_digi", mock_send_product_image_to_digi
        ).start()
        patch.object(DigiClient, "send_product_to_digi", Mock()).start()

        product = self._create_product_with_image("Test Product Template", 400)

        self.assertEqual(mock_send_product_image_to_digi.call_args[0][0], product)

    def _create_product_with_image(self, name, plu_code):
        product_with_image = self.env["product.template"].create(
            {
                "name": name,
                "plu_code": plu_code,
                "list_price": 1.0,
            }
        )
        # Create a 1x1 pixel image
        image = Image.new("RGB", (1, 1))
        output = io.BytesIO()
        image.save(output, format="PNG")
        # Get the binary data of the image
        image_data = base64.b64encode(output.getvalue())
        output.close()
        product_with_image.image_1920 = image_data
        return product_with_image
