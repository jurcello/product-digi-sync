import json

import requests

from odoo import fields, models


class DigiClient(models.Model):
    _name = "digi_sync.digi_client"
    _description = "Digi Client"

    username = fields.Char("@Fresh Username", required=True)
    password = fields.Char("@Fresh Password", required=True)

    def send_product_to_digi(self, product):
        headers = {
            "ApplicationLogIn": json.dumps(
                {"User": self.username, "Password": self.password}
            ),
            "Content-Type": "application/json",
        }
        url = "https://fresh.digi.eu:8010/API/V1/ARTICLE.SVC/POST"
        body = json.dumps([])
        requests.post(url=url, headers=headers, data=body, timeout=30)
