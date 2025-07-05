import re
from html import unescape
from .config import CHAMPS_UTILES, IGNORER_SECTIONS

def nettoyer_html(html):
    if not isinstance(html, str):
        return html
    texte = re.sub(r'<[^>]+>', '', html)
    return unescape(texte).strip()

def filtrer_champs_utiles_recursive(obj):
    if isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            if k in IGNORER_SECTIONS:
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

def filter(data):
    return filtrer_champs_utiles_recursive(data)