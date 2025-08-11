import requests
import json
from typing import Dict, Any, Optional, List
from kanka_api.config import KANKA_API_URL, CAMPAIGN_ID, HEADERS
from kanka_api.utils import kanka_api_request

def create_or_update_character(character_data: Dict[str, Any]) -> Optional[int]:
    """
    Crée ou met à jour un personnage (character) dans Kanka via l'API.
    Si character_data contient déjà un 'id', effectue une mise à jour (PATCH), sinon crée (POST).
    :param character_data: Dictionnaire contenant les champs du personnage (format natif Kanka).
    :return: L'ID du personnage créé ou mis à jour, ou None en cas d'échec.
    """
    is_update = "id" in character_data and character_data["id"] is not None
    if is_update:
        kanka_id = character_data["id"]
        url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/characters/{kanka_id}"
        method = "patch"
    else:
        url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/characters"
        method = "post"

    response = kanka_api_request(method, url, headers=HEADERS, json=character_data)
    if response.status_code in (200, 201):
        kanka_id = response.json()["data"]["id"]
        character_data["id"] = kanka_id
        return kanka_id
    else:
        print(f"Erreur {'mise à jour' if is_update else 'création'} character '{character_data.get('name', '')}': {response.status_code} {response.text}")
        return None

def import_characters_from_file(json_path: str) -> None:
    """
    Importe une liste de personnages depuis un fichier JSON dans Kanka.
    Met à jour le fichier source avec les id Kanka obtenus.
    :param json_path: Chemin du fichier JSON à importer.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        characters_data = json.load(f)

    # On suppose que le fichier contient une liste de personnages (format natif Kanka)
    for character in characters_data:
        create_or_update_character(character)

    # Mise à jour du fichier source avec les id Kanka ajoutés
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(characters_data, f, ensure_ascii=False, indent=2)

def fetch_character_from_kanka(character_id: int) -> (Dict[str, Any], str):
    """
    Récupère un personnage depuis Kanka.
    :param character_id: ID Kanka du personnage.
    :return: Tuple (dictionnaire représentant le personnage, nom du personnage).
    """
    url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/characters/{character_id}"
    response = kanka_api_request('get',url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Erreur récupération character {character_id}: {response.status_code} {response.text}")
    data = response.json()["data"]
    name = data.get("name", "")
    return data, name

# --- Exemple d'utilisation ---
if __name__ == "__main__":
    # Importer tous les personnages d'un fichier
    import_characters_from_file("generated_characters.json")

    # Récupérer un personnage par son ID
    # character = fetch_character_from_kanka(123456)
    # print(json.dumps(character, ensure_ascii=False,