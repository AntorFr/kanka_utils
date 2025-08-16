import os
import re
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

def resoudre_references_kanka(data):
    """
    Remplace les références [type:entity_id] par [type:entity_id|name] 
    en récupérant le nom depuis les données.
    Ne modifie pas les références qui ont déjà un nom [type:entity_id|name].
    
    :param data: Dictionnaire contenant toutes les données Kanka
    :return: Données avec références résolues
    """
    
    # Construire un index entity_id -> name pour tous les types
    entity_index = {}
    
    # Mappage des types de références vers les clés de données
    type_mapping = {
        'character': 'characters',
        'location': 'locations', 
        'organisation': 'organisations',
        'organization': 'organisations',  # Variante anglaise
        'creature': 'creatures',
        'race': 'races',
        'item': 'items',
        'journal': 'journals',
        'note': 'notes',
        'tag': 'tags',
        'map': 'maps',
        'quest': 'quests',
        'event': 'events',
        'vaisseau': 'vaisseau_443',  # Type custom
        'regle': 'regle_446'  # Type custom
    }
    
    # Construire l'index pour chaque type standard
    for ref_type, data_key in type_mapping.items():
        if data_key in data:
            for item in data[data_key]:
                if isinstance(item, dict):
                    # Pour les types standards, utiliser 'id' et chercher 'name'
                    item_id = item.get('id')
                    item_name = item.get('name')
                    
                    # Pour les types custom, extraire depuis 'entity'
                    if 'entity' in item and isinstance(item['entity'], dict):
                        entity = item['entity']
                        item_id = entity.get('id')
                        item_name = entity.get('name')
                    
                    if item_id and item_name:
                        entity_index[f"{ref_type}:{item_id}"] = item_name
    
    # Ajouter un mapping pour les types non standard qu'on trouve dans les données
    for category_key, items in data.items():
        if isinstance(items, list):
            # Extraire le type du nom de catégorie (ex: "vaisseau_443" -> "vaisseau")
            if '_' in category_key:
                type_name = category_key.split('_')[0]
                for item in items:
                    if isinstance(item, dict):
                        item_id = item.get('id')
                        item_name = item.get('name')
                        
                        # Pour les entités custom, chercher dans l'objet 'entity'
                        if 'entity' in item and isinstance(item['entity'], dict):
                            entity = item['entity']
                            item_id = entity.get('id')
                            item_name = entity.get('name')
                        
                        if item_id and item_name:
                            entity_index[f"{type_name}:{item_id}"] = item_name
    
    def remplacer_references_dans_texte(texte):
        """
        Remplace les références [type:id] par [type:id|name] dans un texte.
        """
        if not isinstance(texte, str):
            return texte
            
        # Pattern pour détecter [type:id] mais pas [type:id|name]
        pattern = r'\[([a-zA-Z_]+):(\d+)\](?!\|)'
        
        def remplacer_reference(match):
            ref_type = match.group(1).lower()
            entity_id = match.group(2)
            ref_key = f"{ref_type}:{entity_id}"
            
            # Chercher le nom dans notre index
            name = entity_index.get(ref_key)
            if name:
                return f"[{ref_type}:{entity_id}|{name}]"
            else:
                # Si on ne trouve pas le nom, on laisse la référence telle quelle
                # print(f"⚠️ Référence non résolue: [{ref_type}:{entity_id}]")
                return match.group(0)
        
        return re.sub(pattern, remplacer_reference, texte)
    
    def traiter_recursif(obj):
        """
        Traite récursivement tous les champs de type string dans l'objet.
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str):
                    obj[key] = remplacer_references_dans_texte(value)
                else:
                    traiter_recursif(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    obj[i] = remplacer_references_dans_texte(item)
                else:
                    traiter_recursif(item)
    
    # Traiter toutes les données
    traiter_recursif(data)
    
    print(f"✅ Résolution des références Kanka terminée. Index: {len(entity_index)} entités.")
    
    # Afficher quelques exemples de l'index pour debug
    if entity_index:
        print("📝 Exemples d'entités indexées:")
        for i, (ref, name) in enumerate(list(entity_index.items())[:5]):
            print(f"   {ref} -> {name}")
    
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
    
    # Résoudre les références Kanka [type:id] -> [type:id|name]
    data = resoudre_references_kanka(data)

    return data


