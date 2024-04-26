import base64
import contextlib
import io
import json
from json import JSONDecodeError
from unittest.mock import patch

import requests
from PIL import Image

from odoo.tests import TransactionCase, tagged

from odoo.addons.product_digi_sync.models.digi_client import DigiApiException


class DigiClientTestCase(TransactionCase):
    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.digi_client = self.env["product_digi_sync.digi_client"].create(
            {"username": "test_username", "password": "123", "name": "Default"}
        )

    @tagged("post_install", "-at_install")
    def test_it_can_be_instantiated_with_username_and_password(self):
        self.assertEqual(self.digi_client.password, "123")
        self.assertEqual(self.digi_client.username, "test_username")

    @tagged("post_install", "-at_install")
    def test_it_sends_a_product_to_digi_using_the_right_headers_and_url(self):
        product = self.env["product.product"].create({"name": "Test Product"})

        with self.patch_request_post() as post_spy:
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

        test_category = self.env["product.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 42,
            }
        )

        expected_payload = self._create_expected_product_payload(
            expected_cost_price,
            expected_unit_price,
            ingredients,
            name,
            plu_code,
            test_category.external_digi_id,
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

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_does_not_send_empty_fields(self):
        name = "Test product"
        ingredients = "Noten en zo"
        plu_code = 200

        test_category = self.env["product.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 120,
            }
        )

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
        data["MainGroupDataId"] = test_category.external_digi_id
        data["StatusFields"] = {"PiecesArticle": False}

        expected_payload = json.dumps(data)

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product_without_standard_price)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_does_not_send_empty_ingredients(self):
        name = "Test product"
        plu_code = 200

        test_category = self.env["product.category"].create(
            {
                "name": "Test category",
                "external_digi_id": 120,
            }
        )

        product_without_standard_price = self.env["product.product"].create(
            {
                "name": "Test product",
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
            }
        ]
        data["UnitPrice"] = int(product_without_standard_price.list_price * 100)
        data["MainGroupDataId"] = test_category.external_digi_id
        data["StatusFields"] = {"PiecesArticle": False}

        expected_payload = json.dumps(data)

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product_without_standard_price)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @tagged("post_install", "-at_install")
    def test_it_sends_no_barcode_to_digi_id_if_wrong_format(self):
        barcode_rule = self.env["barcode.rule"].create(
            {
                "name": "Test barcode",
                "encoding": "ean13",
                "type": "price",
                "pattern": ".*",
                "digi_barcode_type_id": 42,
            }
        )

        category = self.env["product.category"].create(
            {
                "name": "Test category",
                "barcode_rule_id": barcode_rule.id,
            }
        )

        product = self.env["product.product"].create(
            {
                "name": "Test product",
                "categ_id": category.id,
            }
        )

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            sended_json = post_spy.call_args.kwargs["data"]
            sended_data = json.loads(sended_json)
            self.assertFalse("NormalBarcode1" in sended_data)

    @tagged("post_install", "-at_install")
    def test_it_sends_the_barcode_digi_id_if_present(self):
        barcode_rule = self.env["barcode.rule"].create(
            {
                "name": "Test barcode",
                "encoding": "ean13",
                "type": "price",
                "pattern": "27.*",
                "digi_barcode_type_id": 42,
            }
        )

        category = self.env["product.category"].create(
            {
                "name": "Test category",
                "barcode_rule_id": barcode_rule.id,
            }
        )

        product = self.env["product.product"].create(
            {
                "name": "Test product",
                "categ_id": category.id,
            }
        )

        expected_data = {
            "NormalBarcode1": {
                "BarcodeDataType": {
                    "Id": 42,
                },
                "Code": 0,
                "DataId": 1,
                "Flag": 27,
                "Type": {
                    "Id": 42,
                },
            }
        }

        with self.patch_request_post() as post_spy:
            self.digi_client.send_product_to_digi(product)

            sent_json = post_spy.call_args.kwargs["data"]
            sent_data = json.loads(sent_json)

            compare_data = {key: sent_data[key] for key in expected_data}

            self.assertEqual(expected_data, compare_data)

    @tagged("post_install", "-at_install")
    def test_it_throws_an_exception_when_request_failed(self):
        product = self.env["product.product"].create({"name": "Test product"})
        response_content = """
                    {
          "Result": -99,
          "ResultDescription": "Invalid_UserPassword",
          "DataId": 0,
          "Post": [],
          "Validation": []
        }
                    """

        with self.patch_request_post(
            status_code=200, response_content=response_content
        ):
            with self.assertRaises(DigiApiException):
                self.digi_client.send_product_to_digi(product)

    @tagged("post_install", "-at_install")
    def test_it_sets_the_result_description_and_code_as_exception_message(self):
        product = self.env["product.product"].create({"name": "Test product"})
        response_content = """
                    {
          "Result": -98,
          "ResultDescription": "Number of filter parameters not correct",
          "DataId": 0,
          "Post": [],
          "Validation": []
        }
                    """

        with self.patch_request_post(
            status_code=200, response_content=response_content
        ):
            with self.assertRaises(DigiApiException) as context:
                self.digi_client.send_product_to_digi(product)
        self.assertEqual(
            str(context.exception), "Error -98: Number of filter parameters not correct"
        )

    def test_it_doesnt_catch_other_exceptions(self):
        product = self.env["product.product"].create({"name": "Test product"})

        with self.patch_request_post(response_content="Invalid json {"):
            with self.assertRaises(JSONDecodeError):
                self.digi_client.send_product_to_digi(product)

    def test_it_sends_a_product_image_to_digi_with_the_right_url(self):
        name = "product Name"
        plu_code = 200
        with self.patch_request_post() as post_spy:
            product_with_image = self._create_product_with_image(name, plu_code)

            expected_url = "https://fresh.digi.eu:8010/API/V1/MultiMedia.SVC/POST"

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["url"], expected_url)

    def test_it_sends_a_product_image_to_digi_with_the_right_payload(self):
        name = "product Name"
        plu_code = 200

        with self.patch_request_post() as post_spy:
            product_with_image = self._create_product_with_image(name, plu_code)

            expected_image_data = product_with_image.image_1920.decode("utf-8")

            payload = {}
            payload["DataId"] = plu_code
            Linknumber_preset_image = 95
            payload["Links"] = [
                {
                    "DataId": plu_code,
                    "LinkNumber": Linknumber_preset_image,
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

            self.digi_client.send_product_image_to_digi(product_with_image)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    def test_it_sends_a_product_image_to_digi_with_the_right_payload_for_jpeg(self):
        name = "product Name"
        plu_code = 200

        with self.patch_request_post() as post_spy:
            product_with_image = self._create_product_with_image_for_jpeg(
                name, plu_code
            )

            expected_image_data = product_with_image.image_1920.decode("utf-8")

            payload = {}
            payload["DataId"] = plu_code
            linknumber_preset_image = 95
            payload["Links"] = [
                {
                    "DataId": plu_code,
                    "LinkNumber": linknumber_preset_image,
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
            payload["InputFormat"] = "jpg"

            expected_payload = json.dumps(payload)

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

        with self.patch_request_post() as post_spy:
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

        with self.patch_request_post() as post_spy:
            self.digi_client.send_category_to_digi(category)

            self.assertEqual(post_spy.call_args.kwargs["data"], expected_payload)

    @contextlib.contextmanager
    def patch_request_post(self, status_code=200, response_content=None):
        if not response_content:
            response_content = json.dumps(
                {
                    "Result": 1,
                    "ResultDescription": "Ok",
                    "DataId": 0,
                    "Post": [],
                    "Validation": [],
                }
            )
        mock_response = requests.Response()
        mock_response.status_code = status_code
        mock_response._content = response_content.encode("utf-8")
        with patch("requests.post", return_value=mock_response) as post_spy:
            yield post_spy

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

    def _create_product_with_image_for_jpeg(self, name, plu_code):
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
        image.save(output, format="jpeg")
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
