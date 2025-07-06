import re
from html import unescape
from .config import CHAMPS_UTILES, CATEGORIES_A_NE_PAS_FILTRER

def nettoyer_html(html):
    if not isinstance(html, str):
        return html
    texte = re.sub(r'<[^>]+>', '', html)
    return unescape(texte).strip()

def filtrer_champs_utiles_recursive(obj):
    # Si la catégorie fait partie des catégories à ne pas filtrer, retourne l'objet tel quel

    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in CATEGORIES_A_NE_PAS_FILTRER:
                result[k] = v
                continue
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

def simplifier_objets_name(obj):
    """
    Parcourt récursivement obj.
    Si un objet (dict) ne contient qu'un champ 'name', il est remplacé par la valeur de ce champ.
    Si une liste ne contient que des objets simplifiables, elle devient une liste de valeurs.
    """
    if isinstance(obj, dict):
        # Si le dict ne contient qu'un champ 'name'
        if set(obj.keys()) == {"name"}:
            return obj["name"]
        # Sinon, on simplifie récursivement ses valeurs
        return {k: simplifier_objets_name(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [simplifier_objets_name(e) for e in obj]
    else:
        return obj


def filter(data):
    data = filtrer_champs_utiles_recursive(data)
    data = simplifier_objets_name(data)
    return data