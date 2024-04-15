import base64
import io
import json
from json import JSONDecodeError
from unittest.mock import patch

from PIL import Image

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

        expected_payload = self._create_expected_product_payload(
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

    def test_it_does_not_send_empty_fields(self):
        name = "Test product"
        ingredients = "Noten en zo"
        plu_code = 200

        test_category = self.env["product.category"].create({"name": "Test category"})

        product_without_standard_price = self.env["product.product"].create(
            {
                "name": "Test product",
                "ingredients": ingredients,
                "plu_code": plu_code,
                "list_price": 1.0,
                "categ_id": test_category.id,
            }
        )

        data = {}
        data["DataId"] = plu_code
        data["Names"] = [
            {
                "Reference": "Nederlands",
                "DdFormatCommodity": f"01000000{name}",
                "DdFormatIngredient": f"01000000{ingredients}",
            }
        ]
        data["UnitPrice"] = int(product_without_standard_price.list_price * 100)
        data["MainGroupDataId"] = test_category.id
        data["StatusFields"] = {"PiecesArticle": False}

        expected_payload = json.dumps(data)

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "{}"

            self.digi_client.send_product_to_digi(product_without_standard_price)

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

    def test_it_sends_a_product_image_to_digi_with_the_right_url(self):
        name = "product Name"
        plu_code = 200

        product_with_image = self._create_product_with_image(name, plu_code)

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "{}"
            expected_url = "https://fresh.digi.eu:8010/API/V1/MultiMedia.SVC/POST"

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)

    def test_it_sends_a_product_image_to_digi_with_the_right_payload(self):
        name = "product Name"
        plu_code = 200

        product_with_image = self._create_product_with_image(name, plu_code)

        expected_image_data = product_with_image.image_1920.decode("utf-8")

        payload = {}
        payload["DataId"] = plu_code
        payload["Links"] = [
            {
                "DataId": plu_code,
                "LinkNumber": 1,
                "Type": {
                    "Description": "Article",
                    "Id": 2,
                },
            }
        ]
        payload["OriginalInput"] = expected_image_data
        payload["Names"] = [
            {
                "DataId": 1,
                "Reference": "Nederlands",
                "Name": "product_name",
            }
        ]
        payload["InputFormat"] = "png"

        expected_payload = json.dumps(payload)

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "{}"

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_a_product_category_to_digi_with_the_right_url(self):
        category_name = "Test category"
        digi_id = 2
        category = self.env["product.category"].create(
            {
                "name": category_name,
                "external_digi_id": digi_id,
            }
        )

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "{}"
            expected_url = "https://fresh.digi.eu:8010/API/V1/MAINGROUP.SVC/POST"

            self.digi_client.send_category_to_digi(category)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)

    def test_it_sends_a_category_digi(self):
        category_name = "Test category"
        digi_id = 2
        category = self.env["product.category"].create(
            {
                "name": category_name,
                "external_digi_id": digi_id,
            }
        )

        payload = {
            "DataId": digi_id,
            "DepartmentId": 97,
            "Names": [
                {
                    "Reference": "Nederlands",
                    "Name": category_name,
                }
            ],
        }

        expected_payload = json.dumps(payload)

        with patch("requests.post") as post_spy:
            post_spy.return_value.status_code = 200
            post_spy.return_value.json.return_value = "{}"
            self.digi_client.send_category_to_digi(category)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def _create_product_with_image(self, name, plu_code):
        product_with_image = self.env["product.product"].create(
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

    def _create_expected_product_payload(
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
