import os
from .config import CATEGORIE_MAP
from .extract import charger_json_depuis_fichier


def normaliser_categorie(data):
    """
    Renomme les catégories à la racine de data selon CATEGORIE_MAP.
    """
    return {
        CATEGORIE_MAP.get(categorie, categorie): objets
        for categorie, objets in data.items()
    }

def marquer_et_tester_prive(obj):
    if isinstance(obj, dict):
        if obj.get("is_private") == 1 or obj.get("visibility_id") == 2:
            obj["prive"] = True
        for v in obj.values():
            marquer_et_tester_prive(v)
    elif isinstance(obj, list):
        for e in obj:
            marquer_et_tester_prive(e)

def fusionner_entity(obj):
    if isinstance(obj, dict):
        if "entity" in obj and isinstance(obj["entity"], dict):
            for sub_k, sub_v in obj["entity"].items():
                obj[sub_k] = sub_v
            del obj["entity"]
        for k, v in obj.items():
            fusionner_entity(v)
    elif isinstance(obj, list):
        for item in obj:
            fusionner_entity(item)


def enrichir_organisations_avec_noms(data):
    """
    Pour chaque organisation, ajoute le champ 'name' à chaque membre en cherchant dans data['characters'].
    La correspondance se fait entre members[].id et organisationMemberships[].id des personnages.
    """
    # On construit un index: organisationMemberships.id -> personnage.name
    id_to_name = {}
    for perso in data.get("characters", []):
        if "organisationMemberships" in perso:
            for membership in perso["organisationMemberships"]:
                if "id" in membership and "name" in perso:
                    id_to_name[membership["id"]] = perso["name"]

    # On enrichit les organisations
    for orga in data.get("organisations", []):
        if "members" in orga:
            for membre in orga["members"]:
                nom = id_to_name.get(membre.get("id"))
                if nom:
                    membre["name"] = nom
    return data

def enrichir_organisationMemberships_avec_nom(data):
    """
    Pour chaque personnage, ajoute le champ 'name' à chaque organisationMemberships
    en cherchant dans data['organisations'] l'organisation qui contient ce membre.
    """
    # On construit un index member_id -> organisation_name
    member_id_to_orga_name = {}
    for orga in data.get("organisations", []):
        orga_name = orga.get("name")
        for member in orga.get("members", []):
            if "id" in member and orga_name:
                member_id_to_orga_name[member["id"]] = orga_name

    # On enrichit les organisationMemberships de chaque personnage
    for perso in data.get("characters", []):
        if "organisationMemberships" in perso:
            for membership in perso["organisationMemberships"]:
                nom = member_id_to_orga_name.get(membership.get("id"))
                if nom:
                    membership["name"] = nom
    return data

def enrichir_organisations(data):
    """
    Enrichit les organisations avec les noms des membres et les noms des organisationsMemberships.
    """
    data = enrichir_organisations_avec_noms(data)
    data = enrichir_organisationMemberships_avec_nom(data)
    return data

def enrichir_tags(data):
    """
    Pour chaque objet contenant 'entityTags', ajoute le champ 'name' à chaque tag en cherchant dans data['tags'].
    La correspondance se fait entre entityTags[].tag_id et tags[].id.
    """
    # On construit un index id -> name pour tous les tags
    tag_id_to_name = {tag["id"]: tag["name"] for tag in data.get("tags", []) if "id" in tag and "name" in tag}

    def enrichir_obj(obj):
        if isinstance(obj, dict):
            if "entityTags" in obj:
                for tag in obj["entityTags"]:
                    nom = tag_id_to_name.get(tag.get("tag_id"))
                    if nom:
                        tag["name"] = nom
            for v in obj.values():
                enrichir_obj(v)
        elif isinstance(obj, list):
            for item in obj:
                enrichir_obj(item)

    enrichir_obj(data)
    return data


def enrichir_locations_contains(data):
    """
    Pour chaque location, ajoute un champ 'contains' qui liste tous les objets dont le champ 'location_id'
    (ou 'location'->'id') correspond à l'id de la location.
    """
    # On récupère la liste des locations
    locations = data.get("locations", [])
    # On prépare une liste de tous les objets à parcourir (hors locations)
    objets_a_tester = []
    for categorie, objets in data.items():
        if categorie != "locations" and isinstance(objets, list):
            objets_a_tester.extend(objets)

    # Pour chaque location, on cherche les objets qui la référencent
    for loc in locations:
        loc_id = loc.get("id") or loc.get("entity_id")
        contains = []
        for obj in objets_a_tester:
            # On teste la présence d'un champ location_id ou d'un champ location avec un id
            if ("location_id" in obj and obj["location_id"] == loc_id) or \
               ("location" in obj and isinstance(obj["location"], dict) and obj["location"].get("id") == loc_id):
                contains.append(obj)
        loc["contains"] = contains
    return data

def enrichir_location_id(data):
    """
    Pour chaque objet contenant 'location_id', remplace ce champ par un objet 'location'
    contenant l'id d'origine et le nom de la location dont l'entity_id correspond à location_id.
    """
    # On construit un index entity_id -> name pour toutes les locations
    entity_id_to_name = {loc["entity_id"]: loc["name"] for loc in data.get("locations", []) if "entity_id" in loc and "name" in loc}

    def enrichir_obj(obj):
        if isinstance(obj, dict):
            if "location_id" in obj:
                loc_id = obj["location_id"]
                obj["location"] = {
                    "id": loc_id,
                    "name": entity_id_to_name.get(loc_id)
                }
                del obj["location_id"]
            for v in obj.values():
                enrichir_obj(v)
        elif isinstance(obj, list):
            for item in obj:
                enrichir_obj(item)

    enrichir_obj(data)
    return data


def enrichir_locations(data):
    """
    Enrichit les locations en ajoutant les objets qu'elles contiennent et en remplaçant location_id par un objet location.
    """
    data = enrichir_locations_contains(data)
    data = enrichir_location_id(data)
    return data

def prepare(data_raw):
    data = data_raw
    #data = normaliser_categorie(data)
    marquer_et_tester_prive(data)
    fusionner_entity(data)

    data = enrichir_organisations(data)
    data = enrichir_tags(data)
    data = enrichir_locations(data)

    return data


