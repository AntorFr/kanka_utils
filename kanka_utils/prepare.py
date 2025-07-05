import os
from .config import CATEGORIE_MAP
from .extract import charger_json_depuis_fichier


def normaliser_categorie(data):
    """
    Renomme les catégories à la racine de data selon CATEGORIE_MAP.
    """
    return {
        CATEGORIE_MAP.get(categorie, categorie): objets
        for categorie, objets in data.items()
    }

def marquer_et_tester_prive(obj):
    if isinstance(obj, dict):
        if obj.get("is_private") == 1 or obj.get("visibility_id") == 2:
            obj["prive"] = True
        for v in obj.values():
            marquer_et_tester_prive(v)
    elif isinstance(obj, list):
        for e in obj:
            marquer_et_tester_prive(e)

def fusionner_entity(obj):
    if isinstance(obj, dict):
        if "entity" in obj and isinstance(obj["entity"], dict):
            for sub_k, sub_v in obj["entity"].items():
                obj[sub_k] = sub_v
            del obj["entity"]
        for k, v in obj.items():
            fusionner_entity(v)
    elif isinstance(obj, list):
        for item in obj:
            fusionner_entity(item)

def prepare(data_raw):
    data = normaliser_categorie(data_raw)
    marquer_et_tester_prive(data)
    fusionner_entity(data)
    return data


