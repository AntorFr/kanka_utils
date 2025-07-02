import os
import zipfile
import json
import shutil
import tempfile
import re
from html import unescape
# === CONFIGURATION ===
ZIP_PATH = "lunivers-deneria_20250702_102015.zip"  # <-- À adapter
OUTPUT_JSON = "univers_eneria_complet.json"
OUTPUT_JSON_FILTERED = "univers_eneria_filtered.json"
OUTPUT_JSONL_TOUT = "univers_eneria_connaissance_privee.jsonl"
OUTPUT_JSONL_PUBLIC = "univers_eneria_connaissance_publique.jsonl"

# === MAPPAGE DES CATÉGORIES LISIBLES ===
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

IGNORER_CATEGORIES_ORIGINE = {"settings", "gallery", "maps"}
IGNORER_CATEGORIES = {CATEGORIE_MAP.get(c, c) for c in IGNORER_CATEGORIES_ORIGINE}

# === CHAMPS AUTORISÉS POUR GPT ===
CHAMPS_UTILES = {"type", "name", "nom", "description", "entry", "contenu", "tags", "résumé", "relation", "catégorie", "titre", "illustration", "prive"}

def extraire_zip(chemin_zip, dossier_temporaire):
    with zipfile.ZipFile(chemin_zip, 'r') as zip_ref:
        zip_ref.extractall(dossier_temporaire)
    return dossier_temporaire

def normaliser_categorie(chemin_fichier):
    parties = os.path.normpath(chemin_fichier).split(os.sep)
    for i in range(len(parties) - 1, 0, -1):
        if parties[i] == "entities":
            dossier_categorie = parties[i - 1]
            return CATEGORIE_MAP.get(dossier_categorie, dossier_categorie)
    return CATEGORIE_MAP.get(parties[-2], parties[-2])

def nettoyer_html(html):
    if not isinstance(html, str):
        return html
    texte = re.sub(r'<[^>]+>', '', html)
    return unescape(texte).strip()

def filtrer_champs_utiles_recursive(obj):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if v is None or v == "":
                continue
            if isinstance(v, (dict, list)):
                v_filtré = filtrer_champs_utiles_recursive(v)
                if v_filtré is not None:
                    result[k] = v_filtré
            elif k in CHAMPS_UTILES:
                if k == "entry":
                    v = nettoyer_html(v)
                result[k] = v
        return result if result else None
    elif isinstance(obj, list):
        liste_filtrée = [filtrer_champs_utiles_recursive(e) for e in obj if e is not None]
        liste_filtrée = [e for e in liste_filtrée if e is not None]
        return liste_filtrée if liste_filtrée else None
        return obj if obj else None

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

def est_prive(contenu):
    return contenu.get("is_private") == 1 or contenu.get("visibility_id") == 2

def charger_et_structurer_json(dossier):
    hiérarchie_filtrée = {}
    hiérarchie_complete = {}
    aplat_prive = []
    aplat_public = []

    for root, _, files in os.walk(dossier):
        for file in files:
            if file.endswith(".json"):
                chemin_fichier = os.path.join(root, file)
                contenu = charger_json_depuis_fichier(chemin_fichier)
                if contenu is None:
                    continue

                categorie = normaliser_categorie(chemin_fichier)
                if categorie in IGNORER_CATEGORIES:
                    continue

                prive = est_prive(contenu)
                contenu_complet = {"type": categorie, **contenu, "prive": prive}
                contenu_filtré = filtrer_champs_utiles_recursive(contenu_complet)

                hiérarchie_complete.setdefault(categorie, []).append(contenu_complet)
                if contenu_filtré:
                    hiérarchie_filtrée.setdefault(categorie, []).append(contenu_filtré)

                nom = contenu.get("name") or contenu.get("nom") or file.replace(".json", "")
                texte = contenu.get("description") or contenu.get("contenu") or json.dumps(contenu_filtré or contenu_complet)

                ligne = {
                    "type": categorie,
                    "nom": nom,
                    "contenu": texte,
                    "prive": prive
                }

                aplat_prive.append(ligne)
                if not prive:
                    aplat_public.append(ligne)

    return hiérarchie_complete, hiérarchie_filtrée, aplat_prive, aplat_public

def sauvegarder_json(data, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sauvegarder_jsonl(lignes, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        for ligne in lignes:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")

def main():
    dossier_temp = tempfile.mkdtemp(prefix="eneria_")
    try:
        extraire_zip(ZIP_PATH, dossier_temp)
        data_complet, data_filtré, jsonl_prive, jsonl_public = charger_et_structurer_json(dossier_temp)

        sauvegarder_json(data_complet, OUTPUT_JSON)
        sauvegarder_json(data_filtré, OUTPUT_JSON_FILTERED)
        sauvegarder_jsonl(jsonl_prive, OUTPUT_JSONL_TOUT)
        sauvegarder_jsonl(jsonl_public, OUTPUT_JSONL_PUBLIC)

        print(f"✅ Fichier complet : {OUTPUT_JSON}")
        print(f"✅ Fichier filtré : {OUTPUT_JSON_FILTERED}")
        print(f"✅ JSONL complet (privé inclus) : {OUTPUT_JSONL_TOUT}")
        print(f"✅ JSONL public uniquement : {OUTPUT_JSONL_PUBLIC}")
    finally:
        shutil.rmtree(dossier_temp)
        print("🧹 Nettoyage terminé.")

if __name__ == "__main__":
    main()
