import json
from json import JSONDecodeError
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.product_digi_sync.models.digi_client import DigiApiException


class DigiClientTestCase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.digi_client = self.env["digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123"}
        )

    @tagged("post_install", "-at_install")
    def test_it_can_be_instantiated_with_username_and_password(self):
        self.assertEqual(self.digi_client.password, "123")
        self.assertEqual(self.digi_client.username, "test_username")

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_using_the_right_headers_and_url(self):
        product = self.env["product.product"].create({"name": "Test Product"})

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "{}"
            expected_url = "https://fresh.digi.eu:8010/API/V1/ARTICLE.SVC/POST"
            expected_headers = {
                "ApplicationLogIn": json.dumps(
                    {"User": "test_username", "Password": "123"}
                ),
                "Content-Type": "application/json",
            }

            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)
            self.assertEqual(post_spy.call_args.kwargs["headers"], expected_headers)

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_with_the_right_payload(self):
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
            post_spy.return_value.json.return_value = "{}"

            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_throws_an_exception_when_request_failed(self):
        product = self.env["product.product"].create({"name": "Test product"})
        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = """
            {
  "Result": -99,
  "ResultDescription": "Invalid_UserPassword",
  "DataId": 0,
  "Post": [],
  "Validation": []
}
            """
            with self.assertRaises(DigiApiException):
                self.digi_client.send_product_to_digi(product)

    @tagged("post_install", "-at_install")
    def test_it_sets_the_result_description_as_exception_message(self):
        product = self.env["product.product"].create({"name": "Test product"})
        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = """
                {
      "Result": -99,
      "ResultDescription": "The result description",
      "DataId": 0,
      "Post": [],
      "Validation": []
    }
                """
            with self.assertRaises(DigiApiException) as context:
                self.digi_client.send_product_to_digi(product)
            self.assertEqual(str(context.exception), "The result description")

    def test_it_doesnt_catch_other_exceptions(self):
        product = self.env["product.product"].create({"name": "Test product"})
        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "Invalid json {"

            with self.assertRaises(JSONDecodeError):
                self.digi_client.send_product_to_digi(product)

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
