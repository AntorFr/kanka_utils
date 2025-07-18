import os
from .config import CATEGORIE_MAP
from .extract import charger_json_depuis_fichier

def est_prive(obj):
    """
    Retourne True si l'objet est privé selon la règle métier (is_private == 1 ou visibility_id == 2).
    """
    return (
        isinstance(obj, dict)
        and (obj.get("is_private") == 1 or obj.get("visibility_id") == 2)
    )

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
        if est_prive(obj):
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
    Pour chaque location, ajoute un champ 'contains' qui liste tous les objets de la catégorie 'locations'
    dont le champ 'location'->'id' est égal à l'entity_id de la location à enrichir.
    Le champ 'contains' est une liste de dicts {id, name (type)}.
    """
    locations = data.get("locations", [])
    # On prépare un index id -> (name, type)
    id_to_info = {
        loc.get("id"): (loc.get("name"), loc.get("type"))
        for loc in locations
        if "id" in loc and "name" in loc and "type" in loc
    }
    for loc in locations:
        entity_id = loc.get("entity_id")
        contains = []
        for other in locations:
            location_field = other.get("location")
            if isinstance(location_field, dict) and location_field.get("id") == entity_id:
                name, typ = id_to_info.get(other.get("id"), (None, None))
                contains.append({
                    "id": other.get("id"),
                    "name": f"{name} ({typ})" if name and typ else name or str(other.get("id"))
                })
        loc["contains"] = contains
    return data

def enrichir_location_id(data):
    """
    Pour chaque objet contenant 'location_id', remplace ce champ par un objet 'location'
    contenant l'id d'origine, le nom de la location et le type entre parenthèses.
    """
    # On construit un index entity_id -> (name, type) pour toutes les locations
    entity_id_to_info = {
        loc["entity_id"]: (loc.get("name"), loc.get("type"))
        for loc in data.get("locations", [])
        if "entity_id" in loc and "name" in loc and "type" in loc
    }

    def enrichir_obj(obj):
        if isinstance(obj, dict):
            if "location_id" in obj:
                loc_id = obj["location_id"]
                name, typ = entity_id_to_info.get(loc_id, (None, None))
                obj["location"] = {
                    "id": loc_id,
                    "name": f"{name} ({typ})" if name and typ else name or str(loc_id)
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

    data = enrichir_location_id(data)
    data = enrichir_locations_contains(data)

    return data

def creer_liaisons_ftl(data):
    """
    Crée une nouvelle catégorie 'FTL' à la racine de data.
    Pour chaque location de type 'System', parcourt ses relationships et ajoute un objet FTL :
    {
        "source": nom du système de départ,
        "target": nom du système d'arrivée (retrouvé via target_id),
        "status": relation,
        "distance": attitude,
        "prive": booléen si présent dans rel, sinon le champ n'est pas ajouté
    }
    """
    locations = data.get("locations", [])
    # Index pour retrouver le nom d'un système à partir de son id
    id_to_name = {loc.get("id"): loc.get("name") for loc in locations if loc.get("type") == "System"}

    ftl_links = []
    for loc in locations:
        if loc.get("type") == "System":
            source_name = loc.get("name")
            for rel in loc.get("relationships", []):
                target_id = rel.get("target_id")
                target_name = id_to_name.get(target_id)
                if source_name and target_name:
                    lien = {
                        "source": source_name,
                        "target": target_name,
                        "status": rel.get("relation"),
                        "distance": rel.get("attitude")
                    }
                    if "prive" in rel:
                        lien["prive"] = rel.get("prive")
                    ftl_links.append(lien)
    data["Liaison FTL"] = ftl_links
    return data

def prepare(data_raw):
    data = data_raw
    #data = normaliser_categorie(data)
    marquer_et_tester_prive(data)
    fusionner_entity(data)

    data = enrichir_organisations(data)
    data = enrichir_tags(data)
    data = enrichir_locations(data)
    data = creer_liaisons_ftl(data)

    return data


