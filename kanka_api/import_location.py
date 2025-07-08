import requests
import json
from typing import Dict, Any, Optional, List
from kanka_api.config import KANKA_API_URL, CAMPAIGN_ID, HEADERS, ICONS_LOCATIONS



def create_location(location_data: Dict[str, Any], parent_id: Optional[int] = None) -> Optional[int]:
    """
    Crée une location dans Kanka via l'API.
    :param location_data: Dictionnaire contenant les champs de la location.
    :param parent_id: ID du parent (location parente) si applicable.
    :return: L'ID de la location créée, ou None en cas d'échec.
    """
    url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/locations"
    payload = {
        "name": location_data["name"],
        "type": location_data.get("type"),
        "entry": location_data.get("entry"),
    }
    if parent_id:
        payload["location_id"] = parent_id

    loc_type = location_data.get("type")
    icon_uuid = ICONS_LOCATIONS.get(loc_type)
    if icon_uuid:
        payload["entity_image_uuid"] = icon_uuid


    response = requests.post(url, headers=HEADERS, json=payload)
    if response.status_code == 201:
        return response.json()["data"]["id"]
    else:
        print(f"Erreur création location '{location_data['name']}': {response.status_code} {response.text}")
        return None

def import_location_tree(location: Dict[str, Any], parent_id: Optional[int] = None) -> Optional[int]:
    """
    Importe récursivement une location et ses enfants dans Kanka.
    :param location: Dictionnaire représentant la location à importer.
    :param parent_id: ID du parent si applicable.
    :return: L'ID de la location créée.
    """
    location_id = create_location(location, parent_id)
    if not location_id:
        return None

    for child in location.get("contains", []):
        import_location_tree(child, parent_id=location_id)
    return location_id

def import_system_from_file(json_path: str) -> None:
    """
    Importe un système stellaire complet depuis un fichier JSON dans Kanka.
    :param json_path: Chemin du fichier JSON à importer.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        system_data = json.load(f)

    # On suppose que la racine est un système (location)
    import_location_tree(system_data)

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    import_system_from_file("generated_systems/Orindor.json")