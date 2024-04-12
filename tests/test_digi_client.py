import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


class DigiClientTestCase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None

    @tagged("post_install", "-at_install")
    def test_it_can_be_instantiated_with_username_and_password(self):
        digi_client = self.env["digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123"}
        )

        self.assertEqual(digi_client.password, "123")
        self.assertEqual(digi_client.username, "test_username")

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_using_the_right_headers_and_url(self):
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

            digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)
            self.assertEqual(post_spy.call_args.kwargs["headers"], expected_headers)

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_with_the_right_payload(self):
        digi_client = self.env["digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123"}
        )

        name = "Test product"
        ingredients = "Noten en zo"
        plu_code = 200
        expected_unit_price = 250
        expected_cost_price = 150

        test_category = self.env["product.category"].create({"name": "Test category"})

        expected_payload = self._create_expected_payload(
            expected_cost_price,
            expected_unit_price,
            ingredients,
            name,
            plu_code,
            test_category.id,
        )

        product = self.env["product.product"].create(
            {
                "name": "Test product",
                "ingredients": ingredients,
                "plu_code": plu_code,
                "categ_id": test_category.id,
                "list_price": 2.5,
                "standard_price": 1.5,
            }
        )

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200

            digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def _create_expected_payload(
        self,
        expected_cost_price,
        expected_unit_price,
        ingredients,
        name,
        plu_code,
        category_id,
    ):
        data = {}
        data["DataId"] = plu_code
        data["Names"] = [
            {
                "Reference": "Nederlands",
                "DdFormatCommodity": f"01000000{name}",
                "DdFormatIngredient": f"01000000{ingredients}",
            }
        ]
        data["UnitPrice"] = expected_unit_price
        data["CostPrice"] = expected_cost_price
        data["MainGroupDataId"] = category_id
        data["StatusFields"] = {"PiecesArticle": False}
        return json.dumps(data)
