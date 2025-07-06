# === CONFIGURATION ===
ZIP_PATH = "lunivers-deneria_20250702_102015.zip"  # <-- À adapter
OUTPUT_JSON = "univers_eneria_complet.json"
OUTPUT_JSON_FILTERED = "univers_eneria_filtered.json"
OUTPUT_JSONL_TOUT = "univers_eneria_connaissance_privee.jsonl"
OUTPUT_PDF_TOUT = "univers_eneria_connaissance_privee.pdf"
OUTPUT_JSONL_PUBLIC = "univers_eneria_connaissance_publique.jsonl"

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