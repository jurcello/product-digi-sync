import json

import requests

from odoo import fields, models

from ..tools.product_transformer import ProductTransformer


class DigiApiException(Exception):
    pass


class DigiClient(models.Model):
    _name = "product_digi_sync.digi_client"
    _description = "Digi Client"

    DEFAULT_FRESH_URL = "https://fresh.digi.eu:8010/API/V1"

    name = fields.Char(required=True)
    username = fields.Char("@Fresh Username", required=True)
    password = fields.Char("@Fresh Password", required=True)
    api_url = fields.Char(required=True, default=DEFAULT_FRESH_URL)

    def send_product_to_digi(self, product):
        self.ensure_one()
        url = self.create_article_url()

        body = ProductTransformer.transform_product_to_payload(product)

        self._post_to_digi(url, body)

    def send_product_image_to_digi(self, product):
        self.ensure_one()
        url = self.create_image_url()

        body = ProductTransformer.transform_product_to_image_payload(product)

        self._post_to_digi(url, body)

    def send_category_to_digi(self, product_category):
        self.ensure_one()
        url = self.create_category_url()

        body = ProductTransformer.transform_product_category_to_payload(
            product_category
        )

        self._post_to_digi(url, body)

    def _post_to_digi(self, url, body):
        headers = self.create_header()
        response = requests.post(
            url=url, headers=headers, data=body, timeout=30, allow_redirects=False
        )
        response_json = response.json()

        if "Result" in response_json and response_json["Result"] != 1:
            raise DigiApiException(
                f"Error {response_json['Result']}: {response_json['ResultDescription']}"
            )

    def create_article_url(self):
        url = f"{self.get_api_url()}/ARTICLE.SVC/POST"
        return url

    def get_api_url(self):
        self.ensure_one()
        return self.api_url if self.api_url else self.DEFAULT_FRESH_URL

    def create_image_url(self):
        url = f"{self.get_api_url()}/MultiMedia.SVC/POST"
        return url

    def create_category_url(self):
        url = f"{self.get_api_url()}/MAINGROUP.SVC/POST"
        return url

    def create_header(self):
        self.ensure_one()
        headers = {
            "ApplicationLogIn": json.dumps(
                {"User": self.username, "Password": self.password}
            ),
            "Content-Type": "application/json",
        }
        return headers
