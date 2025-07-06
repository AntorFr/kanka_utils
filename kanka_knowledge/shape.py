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

def remplacer_references_kanka(text, data):
    """
    Remplace les balises [categorie:id] ou [categorie:id|texte] par le nom trouvé dans data.
    Si l'id n'est pas trouvé dans la catégorie, cherche dans toutes les autres catégories.
    """
    if not isinstance(text, str):
        return text

    def find_name_anywhere(ident):
        for objets in data.values():
            for obj in objets:
                if isinstance(obj, dict) and str(obj.get("id")) == str(ident):
                    return obj.get("name")
        return None

    def find_name(categorie, ident):
        categorie_plural = categorie
        if not categorie_plural.endswith('s'):
            categorie_plural += 's'
        objets = data.get(categorie_plural, [])
        for obj in objets:
            if str(obj.get("id")) == str(ident):
                return obj.get("name")
        # Si non trouvé, cherche partout
        return find_name_anywhere(ident)

    def replacer(match):
        categorie = match.group(1)
        ident = match.group(2)
        nom = find_name(categorie, ident)
        return nom if nom else match.group(0)

    # Gère aussi les balises avec |texte
    return re.sub(r"\[([a-z_]+):(\d+)(?:\|[^\]]*)?\]", replacer, text)

def appliquer_remplacement_references(data, data_ref):
    """
    Parcourt récursivement data, applique remplacer_references_kanka à chaque champ 'entry'.
    data_ref est la structure de référence pour le remplacement.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k == "entry" and isinstance(v, str):
                data[k] = remplacer_references_kanka(v, data_ref)
            else:
                appliquer_remplacement_references(v, data_ref)
    elif isinstance(data, list):
        for item in data:
            appliquer_remplacement_references(item, data_ref)
    # Si ce n'est ni dict ni list, rien à faire
    return data

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

    data = appliquer_remplacement_references(data, data)
    data = supprimer_champs(data)

    for categorie, objets in data.items():
        for obj in objets:
            nom = obj.get("name") or obj.get("nom") or ""
            texte_prive = obj.get("description") or obj.get("contenu") or formater_texte(obj)
            texte_public = None
            if not obj.get("prive"):
                texte_public = obj.get("description") or obj.get("contenu") or formater_texte(obj)

            ligne = {
                "type": categorie,
                "contenu": texte_prive,
            }
            if nom:
                ligne["titre"] = nom
            aplat_prive.append(ligne)

            if texte_public:
                ligne_public = {
                    "type": categorie,
                    "contenu": texte_public
                }
                if nom:
                    ligne_public["titre"] = nom
                aplat_public.append(ligne_public)

    return aplat_prive, aplat_public
