import json

import requests

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
        headers = self.create_header()
        url = self.create_article_url()

        body = ProductTransformer.transform_product_to_payload(product)

        response = requests.post(
            url=url, headers=headers, data=body, timeout=30, allow_redirects=False
        )
        response_json = json.loads(response.json())

        if "Result" in response_json and response_json["Result"] == -99:
            raise DigiApiException(response_json["ResultDescription"])

    def create_article_url(self):
        url = f"{self.FRESH_URL}/ARTICLE.SVC/POST"
        return url

    def create_header(self):
        headers = {
            "ApplicationLogIn": json.dumps(
                {"User": self.username, "Password": self.password}
            ),
            "Content-Type": "application/json",
        }
        return headers
