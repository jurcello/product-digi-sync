import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


class DigiClientTestCase(TransactionCase):
    @tagged("post_install", "-at_install")
    def test_it_can_be_instantiated_with_username_and_password(self):
        digi_client = self.env["digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123"}
        )

        self.assertEqual(digi_client.password, "123")
        self.assertEqual(digi_client.username, "test_username")

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_using_the_right_headers(self):
        product = self.env["product.product"].create({"name": "Test Product"})

        digi_client = self.env["digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123"}
        )

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            expected_url = "https://fresh.digi.eu:8010/API/V1/ARTICLE.SVC/POST"
            expected_headers = {
                "ApplicationLogIn": json.dumps(
                    {"User": "test_username", "Password": "123"}
                ),
                "Content-Type": "application/json",
            }
            expected_body = json.dumps([])

            digi_client.send_product_to_digi(product)

            post_spy.assert_called_once_with(
                url=expected_url,
                headers=expected_headers,
                data=expected_body,
                timeout=30,
            )
