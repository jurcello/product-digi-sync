import base64
import io
import json

from PIL import Image


class ProductTransformer:
    @classmethod
    def transform_product_to_payload(self, product):
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

        return json.dumps(data)

    @classmethod
    def transform_product_to_image_payload(cls, product):
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
        return json.dumps(payload)

    @classmethod
    def transform_product_category_to_payload(cls, product_category):
        payload = {
            "DataId": product_category.external_digi_id,
            "DepartmentId": 97,
            "Names": [
                {
                    "Reference": "Nederlands",
                    "Name": product_category.name,
                }
            ],
        }
        return json.dumps(payload)
