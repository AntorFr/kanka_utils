import os
import json
from kanka_agent.config import GENERATED_SYSTEM_DIR, GENERATED_CHARACTERS_DIR

def save_system_json(systeme, nom_systeme):
    save_json(systeme, nom_systeme, GENERATED_SYSTEM_DIR)

def save_character_json(character, nom_character):
    save_json(character, nom_character, GENERATED_CHARACTERS_DIR)

def save_json(data,nom ,path):
    """
    Enregistre le système généré dans un fichier JSON dans le dossier configuré.
    """
    if not os.path.exists(path):
        os.makedirs(path)
    chemin_fichier = os.path.join(path, f"{nom}.json")
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Système sauvegardé dans {chemin_fichier}")