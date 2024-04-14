import base64
import io
import json

import requests
from PIL import Image

from odoo import fields, models

from ..tools.product_transformer import ProductTransformer


class DigiApiException(Exception):
    pass


class DigiClient(models.Model):
    _name = "digi_sync.digi_client"
    _description = "Digi Client"

    FRESH_URL = "https://fresh.digi.eu:8010/API/V1"

    username = fields.Char("@Fresh Username", required=True)
    password = fields.Char("@Fresh Password", required=True)

    def send_product_to_digi(self, product):
        url = self.create_article_url()

        body = ProductTransformer.transform_product_to_payload(product)

        self._post_to_digi(url, body)

    def send_product_image_to_digi(self, product):
        url = self.create_image_url()

        image_name = product.name.lower().replace(" ", "_")
        payload = {"DataId": product.plu_code}
        image_data = base64.b64decode(product.image_1920)
        image = Image.open(io.BytesIO(image_data))
        image_format = image.format.lower()
        payload["Links"] = [
            {
                "DataId": product.plu_code,
                "LinkNumber": 1,
                "Type": {
                    "Description": "Article",
                    "Id": 2,
                },
            }
        ]
        payload["OriginalInput"] = product.image_1920.decode("utf-8")
        payload["Names"] = [
            {
                "DataId": 1,
                "Reference": "Nederlands",
                "Name": image_name,
            }
        ]
        payload["InputFormat"] = image_format

        self._post_to_digi(url, json.dumps(payload))

    def _post_to_digi(self, url, body):
        headers = self.create_header()
        response = requests.post(
            url=url, headers=headers, data=body, timeout=30, allow_redirects=False
        )
        response_json = json.loads(response.json())
        if "Result" in response_json and response_json["Result"] == -99:
            raise DigiApiException(response_json["ResultDescription"])

    def create_article_url(self):
        url = f"{self.FRESH_URL}/ARTICLE.SVC/POST"
        return url

    def create_image_url(self):
        url = f"{self.FRESH_URL}/MultiMedia.SVC/POST"
        return url

    def create_header(self):
        headers = {
            "ApplicationLogIn": json.dumps(
                {"User": self.username, "Password": self.password}
            ),
            "Content-Type": "application/json",
        }
        return headers
