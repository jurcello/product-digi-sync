import json


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
