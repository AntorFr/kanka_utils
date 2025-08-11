import shutil, os , json

from kanka_knowledge.config import ZIP_PATH, OUTPUT_JSON, OUTPUT_JSON_FILTERED, OUTPUT_JSONL_TOUT, OUTPUT_JSONL_PUBLIC, OUTPUT_PDF_TOUT
from kanka_knowledge.extract import extract
from kanka_knowledge.prepare import prepare
from kanka_knowledge.export import export_json, export_jsonl, export_pdf
from kanka_knowledge.filter import filter
from kanka_knowledge.shape import shape

from kanka_agent.rag_utils import create_rag_index
from kanka_agent.system_agent import SWNAgent

from kanka_api.location import import_system_from_file, import_location_tree, fetch_location_from_kanka, export_all_systems_from_kanka, import_location_from_file
from kanka_api.character import import_characters_from_file, create_or_update_character, fetch_character_from_kanka

from kanka_agent.export import save_system_json, save_character_json
from kanka_agent.config import GENERATED_SYSTEM_DIR

def update_knowledge_base():
    """
    Met à jour la base de connaissance locale et l'index RAG.
    """
    try:
        dossier_temp, data = extract(ZIP_PATH)
        data = prepare(data)
        export_json(data, OUTPUT_JSON)
        filtered_data = filter(data)
        export_json(filtered_data, OUTPUT_JSON_FILTERED)

        aplat_prive, aplat_public = shape(filtered_data)
        export_jsonl(aplat_prive, OUTPUT_JSONL_TOUT)
        #export_pdf(aplat_prive, OUTPUT_PDF_TOUT)
        create_rag_index(OUTPUT_JSONL_TOUT)

        export_jsonl(aplat_public, OUTPUT_JSONL_PUBLIC)
        print("✅ Export terminé.")
    finally:
        shutil.rmtree(dossier_temp)
        print("🧹 Nettoyage terminé.")

def generate_system(nom_systeme: str = "", contexte=None):
    """
    Génère un système stellaire et l'importe dans Kanka.
    """
    agent = SWNAgent()
    systeme, nom_systeme = agent.generate_system(nom_systeme, contexte)
    import_location_tree(systeme)
    save_system_json(systeme, nom_systeme)
    print(f"✅ Système '{nom_systeme}' généré et importé.")

def generate_structure(nom_structure: str = "", type_structure: str = "", contexte=None, location: str = ""):
    """
    Génère une structure artificielle et l'importe dans Kanka.
    """
    agent = SWNAgent()
    structure, nom = agent.generate_structure(nom_structure, type_structure, contexte, location)
    import_location_tree(structure)
    save_system_json(structure, nom)
    print(f"✅ Structure '{nom}' générée et importée.")

def export_system_from_kanka(location_id: int):
    """
    Exporte un système depuis Kanka et le sauvegarde en JSON.
    """
    systeme, nom = fetch_location_from_kanka(location_id)
    save_system_json(systeme, nom)
    print(f"✅ Système '{nom}' exporté depuis Kanka.")

def export_all_systems():
    """
    Exporte tous les systèmes de la campagne Kanka.
    """
    export_all_systems_from_kanka()
    print("✅ Tous les systèmes ont été exportés.")

def import_system(nom_systeme: str):
    """
    Importe un système depuis un fichier JSON dans Kanka.
    """
    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_systeme}.json")
    import_system_from_file(json_path)
    print(f"✅ Système importé depuis {json_path}.")

def import_location(nom_location: str, parent_id: int = None):
    """
    Importe une location depuis un fichier JSON dans Kanka.
    """
    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_location}.json")
    from kanka_api.location import import_location_from_file
    location_id = import_location_from_file(json_path, parent_id)
    print(f"✅ Location importée depuis {json_path} (ID Kanka : {location_id}).")

def import_characters(json_path: str):
    """
    Importe des personnages depuis un fichier JSON dans Kanka.
    """
    import_characters_from_file(json_path)
    print(f"✅ Personnages importés depuis {json_path}.")

def enrich_system(nom_systeme: str, prompt: str, contexte=None):
    """
    Enrichit un système existant à partir de son nom et d'un prompt, puis sauvegarde le résultat.
    """
    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_systeme}.json")
    agent = SWNAgent()
    
    # Charger le système existant
    with open(json_path, "r", encoding="utf-8") as f:
        original_system = json.load(f)
    
    # Faire l'enrichissement
    enriched_system, nom = agent.enrich_system(original_system, prompt, contexte)
    
    # Préserver les IDs existants
    def preserve_existing_ids(original, enriched):
        if isinstance(original, dict) and isinstance(enriched, dict):
            if "id" in original:
                enriched["id"] = original["id"]
            if "contains" in original and "contains" in enriched:
                original_by_name = {item.get("name"): item for item in original.get("contains", []) if isinstance(item, dict)}
                for enriched_item in enriched.get("contains", []):
                    if isinstance(enriched_item, dict):
                        name = enriched_item.get("name")
                        if name in original_by_name:
                            preserve_existing_ids(original_by_name[name], enriched_item)
        return enriched
    
    # Préserver les IDs existants
    enriched_system = preserve_existing_ids(original_system, enriched_system)
    
    # Forcer les propriétés originales critiques pour éviter les changements non désirés
    enriched_system["name"] = original_system["name"]  # Nom original
    enriched_system["type"] = original_system["type"]  # Type original
    if "id" in original_system:
        enriched_system["id"] = original_system["id"]  # ID original
    
    save_system_json(enriched_system, nom_systeme)
    print(f"✅ Système '{nom_systeme}' enrichi et sauvegardé dans {json_path}.")

def enrich_structure(nom_structure: str, prompt: str, contexte=None, location: str = ""):
    """
    Enrichit une structure existante à partir de son nom, d'un prompt et éventuellement d'un contexte/location, puis sauvegarde le résultat.
    """
    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_structure}.json")
    agent = SWNAgent()
    with open(json_path, "r", encoding="utf-8") as f:
        structure_json = json.load(f)
    enriched_structure, nom = agent.enrich_structure(structure_json, prompt, contexte, location)
    save_system_json(enriched_structure, nom)
    print(f"✅ Structure '{nom}' enrichie et sauvegardée dans {json_path}.")

def generate_system_synthesis(nom_systeme: str):
    """
    Génère une synthèse automatique du système en analysant son contenu et en créant des liens Kanka.
    """
    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_systeme}.json")
    
    with open(json_path, "r", encoding="utf-8") as f:
        system_data = json.load(f)
    
    if "id" not in system_data:
        print(f"❌ Le système '{nom_systeme}' n'a pas d'ID Kanka. Importez-le d'abord.")
        return
    
    # Utiliser l'agent pour générer la synthèse
    agent = SWNAgent()
    updated_entry = agent.generate_system_synthesis(system_data)
    
    # Mettre à jour le système
    system_data["entry"] = updated_entry
    
    # Sauvegarder
    save_system_json(system_data, nom_systeme)
    
    # Compter les éléments pour l'affichage
    total_elements = 0
    if "contains" in system_data:
        def count_elements(container):
            count = len(container.get("contains", []))
            for item in container.get("contains", []):
                count += count_elements(item)
            return count
        total_elements = count_elements(system_data)
    
    print(f"✅ Synthèse générée pour le système '{nom_systeme}' avec {total_elements} éléments liés.")
    return updated_entry

def main():
    # Choisis ici l'action à effectuer
    # Exemple d'utilisation :
    # update_knowledge_base()
    # generate_system(nom_systeme="Sol", contexte=["Contexte système Sol"])
    # generate_structure(nom_structure="Dôme de Balor", type_structure="Colonie", contexte=["Vortex Armatum", "Centre de test d'armemement de Vortex Armatum", "200 personnes y travail"], location="Kheron")
    # export_system_from_kanka(1757370)
    # export_all_systems()
    #import_system("Ephyros")
    # import_characters("generated_characters.json")
    #enrich_system("Ephyros", "Enrichie le system Ephyros", contexte=[])
    #enrich_structure("Chantiers Orbitaux de Clyra", "Ajoute la description des chantiers", contexte=["Stellarion Dynamics"])
    #import_location("Chantiers Orbitaux de Clyra")
    
    # Export du système Aureon depuis Kanka pour récupérer les entity_id
    export_system_from_kanka(1757369)  # ID Kanka d'Aureon
    
    # Génération de synthèse pour le système Aureon (maintenant avec entity_id)
    generate_system_synthesis("Aureon")
    
    # Mise à jour du système dans Kanka avec la synthèse générée
    import_system("Aureon")
    
    # Pour l'exemple, on lance la mise à jour de la base de connaissance :
    #update_knowledge_base()

if __name__ == "__main__":
    main()


