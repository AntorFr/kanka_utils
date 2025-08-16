# === CONFIGURATION ===
import os
import glob
from typing import Optional

def get_latest_zip_path() -> str:
    """
    Trouve automatiquement le fichier ZIP le plus récent au format lunivers-deneria_YYYYMMDD_HHMMSS.zip
    :return: Chemin vers le fichier ZIP le plus récent
    :raises FileNotFoundError: Si aucun fichier ZIP correspondant n'est trouvé
    """
    # Chercher tous les fichiers ZIP correspondant au pattern
    pattern = "lunivers-deneria_*_*.zip"
    zip_files = glob.glob(pattern)
    
    if not zip_files:
        raise FileNotFoundError(f"Aucun fichier ZIP trouvé correspondant au pattern '{pattern}'")
    
    # Trier par date de modification (le plus récent en dernier)
    zip_files.sort(key=lambda f: os.path.getmtime(f))
    
    latest_zip = zip_files[-1]
    print(f"📁 Fichier ZIP le plus récent détecté : {latest_zip}")
    return latest_zip

# Utilisation dynamique du fichier ZIP le plus récent
ZIP_PATH = get_latest_zip_path()
OUTPUT_JSON = "univers_eneria_complet.json"
OUTPUT_JSON_FILTERED = "univers_eneria_filtered.json"
OUTPUT_JSONL_TOUT = "univers_eneria_connaissance_privee.jsonl"
OUTPUT_PDF_TOUT = "univers_eneria_connaissance_privee.pdf"
OUTPUT_MARKDOWN = "univers_eneria_connaissance.md"
OUTPUT_JSONL_PUBLIC = "univers_eneria_connaissance_publique.jsonl"
OUTPUT_FTL_JSON = "univers_eneria_reseau_ftl.json"

# === MAPPAGE DES CATÉGORIES LISIBLES ===
IGNORER_CATEGORIES = {"settings", "gallery", "maps"}
IGNORER_SECTIONS = {"character_races", "organisation_memberships", "mentions"}
CATEGORIES_A_NE_PAS_FILTRER = {"Liaison FTL"}

CATEGORIE_MAP = {
    "characters": "personnage",
    "locations": "lieu",
    "organisations": "organisation",
    "creatures": "créature",
    "races": "race",
    "items": "objet",
    "maps": "carte",
    "journals": "événement",
    "notes": "note",
    "gallery": "illustration",
    "tags": "tag",
}



# === CHAMPS AUTORISÉS POUR GPT ===
CHAMPS_UTILES = {"type", "name", "nom", "description", "entry", "contenu", "tags", "relation",
                "catégorie", "titre", "illustration", "prive","members","is_destroyed","is_dead","entity_id"} #"entity_id","id"

CHAMPS_A_SUPPRIMER_DU_JSONL = ["entity_id", "id","mentions"]