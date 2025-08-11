import requests
import json
from typing import Dict, Any, Optional, List
from kanka_api.config import KANKA_API_URL, CAMPAIGN_ID, HEADERS, ICONS_LOCATIONS
from kanka_agent.export import save_system_json
from kanka_api.utils import kanka_api_request

def export_all_systems_from_kanka() -> None:
    """
    Exporte tous les systèmes (locations de type 'System') de la campagne Kanka.
    Pour chaque système, récupère l'arbre complet et l'enregistre en JSON via save_system_json.
    :param save_dir: Dossier où sauvegarder les fichiers JSON.
    """
    
    # Récupérer toutes les locations de la campagne (pagination)
    all_locations = []
    page = 1
    while True:
        url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/locations"
        resp = kanka_api_request('get',url, headers=HEADERS, params={"page": page})
        if resp.status_code != 200:
            raise Exception(f"Erreur récupération des locations (page {page}): {resp.status_code} {resp.text}")
        data = resp.json()
        all_locations.extend(data["data"])
        if not data.get("links", {}).get("next"):
            break
        page += 1

    # Filtrer les systèmes
    systems = [loc for loc in all_locations if loc.get("type") == "System"]

    print(f"🔎 {len(systems)} systèmes trouvés.")

    for system in systems:
        system_json, system_name = fetch_location_from_kanka(system["id"])
        save_system_json(system_json, system_name)
        print(f"✅ Système '{system_name}' exporté.")

def fetch_location_from_kanka(location_id: int) -> (Dict[str, Any], str):
    """
    Récupère une location et ses enfants récursivement depuis Kanka pour produire un JSON hiérarchique.
    :param location_id: ID Kanka de la location racine.
    :return: Tuple (dictionnaire représentant la location et ses enfants, nom de la location)
    """
    # Récupérer la location principale
    url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/locations/{location_id}?related=locations"
    response = kanka_api_request('get',url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Erreur récupération location {location_id}: {response.status_code} {response.text}")
    data = response.json()["data"]

    # Champs principaux
    location_json = {
        "name": data["name"],
        "type": data.get("type"),
        "entry": data.get("entry"),
        "id": data["id"]
    }

    # Récupérer les enfants (locations dont le parent est cette location)
    children = []
    # Kanka retourne les enfants dans data["locations"] si ?related=locations
    for child in data.get("children", []):
        # Pour chaque enfant, appel récursif
        children.append(fetch_location_from_kanka(child)[0])
    if children:
        location_json["contains"] = children

    return location_json, location_json["name"]

def create_location(location_data: Dict[str, Any], parent_id: Optional[int] = None) -> Optional[int]:
    """
    Crée ou met à jour une location dans Kanka via l'API.
    Si location_data contient déjà un 'id', effectue une mise à jour (PATCH), sinon crée (POST).
    :param location_data: Dictionnaire contenant les champs de la location.
    :param parent_id: ID du parent (location parente) si applicable.
    :return: L'ID de la location créée ou mise à jour, ou None en cas d'échec.
    """
    is_update = "id" in location_data and location_data["id"] is not None
    if is_update:
        # Mise à jour (PATCH)
        kanka_id = location_data["id"]
        url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/locations/{kanka_id}"
        method = "patch"
    else:
        # Création (POST)
        url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/locations"
        method = "post"

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

    response = kanka_api_request(method,url, headers=HEADERS, json=payload)
    if response.status_code in (200, 201):
        kanka_id = response.json()["data"]["id"]
        location_data["id"] = kanka_id
        return kanka_id
    else:
        print(f"Erreur {'mise à jour' if is_update else 'création'} location '{location_data['name']}': {response.status_code} {response.text}")
        return None

def import_location_from_file(json_path: str, parent_id: Optional[int] = None) -> Optional[int]:
    """
    Importe une location unique depuis un fichier JSON dans Kanka.
    Utilise create_location pour l'importer et met à jour le fichier avec l'id Kanka obtenu.
    :param json_path: Chemin du fichier JSON à importer.
    :param parent_id: ID du parent (location parente) si applicable.
    :return: L'ID de la location créée ou mise à jour, ou None en cas d'échec.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        location_data = json.load(f)

    location_id = create_location(location_data, parent_id)

    # Mise à jour du fichier source avec l'id Kanka ajouté
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(location_data, f, ensure_ascii=False, indent=2)

    return location_id

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
    Met à jour le fichier source avec les id Kanka obtenus.
    :param json_path: Chemin du fichier JSON à importer.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        system_data = json.load(f)

    # On suppose que la racine est un système (location)
    import_location_tree(system_data)

    # Mise à jour du fichier source avec les id Kanka ajoutés
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(system_data, f, ensure_ascii=False, indent=2)

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    import_system_from_file("generated_systems/Sol.json")