import zipfile
import tempfile
import json, os 

from .config import ZIP_PATH, IGNORER_CATEGORIES


def extract_zip(fichier_zip):
    dossier_temp = tempfile.mkdtemp(prefix="eneria_")
    with zipfile.ZipFile(fichier_zip, 'r') as zip_ref:
        zip_ref.extractall(dossier_temp)
    return dossier_temp

def charger_json_depuis_fichier(chemin_fichier):
    try:
        with open(chemin_fichier, "r", encoding="utf-8") as f:
            raw = f.read().strip()
            if not raw:
                print(f"[IGNORÉ] {chemin_fichier} : fichier vide")
                return None
            try:
                contenu = json.loads(raw)
                if isinstance(contenu, str):
                    contenu = json.loads(contenu)
                return contenu
            except json.JSONDecodeError as e:
                print(f"[ERREUR] {chemin_fichier} : fichier JSON invalide — {e}")
                return None
    except Exception as e:
        print(f"[ERREUR] {chemin_fichier} : {e}")
        return None
    
def get_categorie(chemin_fichier):
    parties = os.path.normpath(chemin_fichier).split(os.sep)
    for i in range(len(parties) - 1, 0, -1):
        if parties[i] == "entities":
            dossier_categorie = parties[i - 1]
            return dossier_categorie
    return parties[-2]

def charger_json(dossier):
    raw_concact = {} 

    for root, _, files in os.walk(dossier):
        for file in files:
            if file.endswith(".json"):
                chemin_fichier = os.path.join(root, file)
                contenu = charger_json_depuis_fichier(chemin_fichier)
                if contenu is None:
                    continue

                categorie = get_categorie(chemin_fichier)
                    
                if categorie in IGNORER_CATEGORIES:
                    continue

                contenu_complet = {"categorie": categorie, **contenu,}
                
                raw_concact.setdefault(categorie, []).append(contenu_complet)
                
    return raw_concact


def extract(fichier_zip=ZIP_PATH):
    dossier_temp = extract_zip(fichier_zip)
    raw = charger_json(dossier_temp)
    return dossier_temp, raw