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

        data = {}
        data["DataId"] = product.plu_code
        data["Names"] = [
            {
                "Reference": "Nederlands",
                "DdFormatCommodity": f"01000000{product.name}",
                "DdFormatIngredient": f"01000000{product.ingredients}",
            }
        ]
        if product.list_price:
            data["UnitPrice"] = int(product.list_price * 100)
        if product.standard_price:
            data["CostPrice"] = int(product.standard_price * 100)
        if product.categ_id.id:
            data["MainGroupDataId"] = product.categ_id.id
        data["StatusFields"] = {"PiecesArticle": False}

        body = json.dumps(data)
        requests.post(url=url, headers=headers, data=body, timeout=30)