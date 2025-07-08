import requests
from typing import List, Dict, Any
from dotenv import load_dotenv
from kanka_api.config import KANKA_API_URL,CAMPAIGN_ID, HEADERS


def list_campaigns() -> List[Dict[str, Any]]:
    """
    Récupère la liste des campagnes Kanka accessibles avec le token fourni.
    :return: Liste de dictionnaires représentant les campagnes.
    """
    url = f"{KANKA_API_URL}/campaigns"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        return data.get("data", [])
    else:
        print(f"Erreur lors de la récupération des campagnes : {response.status_code} {response.text}")
        return []

def list_images() -> List[Dict[str, Any]]:
    """
    Récupère la liste des images de la librairie Kanka (Asset Library).
    :return: Liste de dictionnaires avec 'name' et 'uuid' pour chaque image.
    """
    url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/images"
    response = requests.get(url, headers=HEADERS)
    images = []
    if response.status_code == 200:
        try:
            data = response.json()
            for asset in data.get("data", []):
                images.append({
                    "name": asset.get("name"),
                    "id": asset.get("id")
                })
        except Exception:
            print(f"Réponse non JSON ou vide : {response.status_code} {response.text}")
    else:
        print(f"Erreur lors de la récupération des images : {response.status_code} {response.text}")
    return images

def main():
    """
    Fonction principale pour tester les appels API.
    """
    print("Campagnes disponibles :")
    for camp in list_campaigns():
        print(f"- {camp['id']}: {camp['name']}")
    
    print("\nImages de la librairie :")
    for img in list_images():
        print(f"- {img['name']} : {img['id']}")

# Exemple d'utilisation :
if __name__ == "__main__":
    main()