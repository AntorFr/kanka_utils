import os
import json
from kanka_agent.config import GENERATED_SYSTEM_DIR

def save_system_json(systeme, nom_systeme):
    """
    Enregistre le système généré dans un fichier JSON dans le dossier configuré.
    """
    if not os.path.exists(GENERATED_SYSTEM_DIR):
        os.makedirs(GENERATED_SYSTEM_DIR)
    chemin_fichier = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_systeme}.json")
    with open(chemin_fichier, "w", encoding="utf-8") as f:
        json.dump(systeme, f, ensure_ascii=False, indent=2)
    print(f"Système sauvegardé dans {chemin_fichier}")