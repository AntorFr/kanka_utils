import re
from .config import CHAMPS_A_SUPPRIMER_DU_JSONL

def flatten_data(data_filtré):
    aplat_prive = []
    aplat_public = []

    for categorie, objets in data_filtré.items():
        for obj in objets:
            nom = obj.get("name") or obj.get("nom")
            texte_prive = obj.get("description") or obj.get("contenu")
            texte_public = obj.get("contenu") if not obj.get("prive") else None

            ligne = {
                "categorie": categorie,
                "nom": nom,
                "contenu": texte_prive,
            }
            aplat_prive.append(ligne)

            if texte_public:
                ligne_public = {
                    "categorie": categorie,
                    "nom": nom,
                    "contenu": texte_public
                }
                aplat_public.append(ligne_public)

    return aplat_prive, aplat_public

def formater_texte(obj, prefix=""):
    if isinstance(obj, dict):
        lignes = []
        for k, v in obj.items():
            if isinstance(v, (dict, list)):
                sous_texte = formater_texte(v, prefix + "  ")
                lignes.append(f"{prefix}{k} :\n{sous_texte}")
            else:
                lignes.append(f"{prefix}{k} : {v}")
        return "\n".join(lignes)
    elif isinstance(obj, list):
        return "\n".join(f"{prefix}- {formater_texte(v, prefix + '  ')}" for v in obj)
    else:
        return f"{prefix}{obj}"
    
def supprimer_objets_prives(obj):
    if isinstance(obj, dict):
        if obj.get("prive"):
            return None
        result = {}
        for k, v in obj.items():
            v_filtré = supprimer_objets_prives(v)
            if v_filtré is not None:
                result[k] = v_filtré
        return result if result else None
    elif isinstance(obj, list):
        return [e for e in (supprimer_objets_prives(e) for e in obj) if e is not None]
    return obj


def construire_index_noms(data_complet):
    index = {}
    for categorie, objets in data_complet.items():
        for obj in objets:
            if "id" in obj and ("name" in obj or "nom" in obj):
                nom = obj.get("name") or obj.get("nom")
                index[(categorie, str(obj["id"]))] = nom
    return index

def remplacer_references_kanka(text, index):
    if not isinstance(text, str):
        return text

    def replacer(match):
        type_ref = match.group(1)
        ident = match.group(2)
        nom = index.get((type_ref, ident))
        return f"{nom} ({type_ref})" if nom else match.group(0)

    return re.sub(r"\[([a-z_]+):(\d+)\]", replacer, text)

def supprimer_champs(obj, champs_a_supprimer=CHAMPS_A_SUPPRIMER_DU_JSONL):
    """
    Supprime récursivement les champs listés dans champs_a_supprimer de tous les dictionnaires de l'objet.
    """
    if isinstance(obj, dict):
        for champ in champs_a_supprimer:
            obj.pop(champ, None)
        for v in obj.values():
            supprimer_champs(v, champs_a_supprimer)
    elif isinstance(obj, list):
        for item in obj:
            supprimer_champs(item, champs_a_supprimer)
    return obj

def shape(data):
    aplat_prive = []
    aplat_public = []

    data = supprimer_champs(data)

    for categorie, objets in data.items():
        for obj in objets:
            nom = obj.get("name") or obj.get("nom") or ""
            texte_prive = obj.get("description") or obj.get("contenu") or formater_texte(obj)
            texte_public = None
            if not obj.get("prive"):
                texte_public = obj.get("description") or obj.get("contenu") or formater_texte(obj)

            ligne = {
                "categorie": categorie,
                "nom": nom,
                "contenu": texte_prive,
            }
            aplat_prive.append(ligne)

            if texte_public:
                ligne_public = {
                    "categorie": categorie,
                    "nom": nom,
                    "contenu": texte_public
                }
                aplat_public.append(ligne_public)

    return aplat_prive, aplat_public
