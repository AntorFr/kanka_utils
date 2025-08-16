import shutil, os , json, copy

from kanka_knowledge.config import ZIP_PATH, OUTPUT_JSON, OUTPUT_JSON_FILTERED, OUTPUT_JSONL_TOUT, OUTPUT_JSONL_PUBLIC, OUTPUT_PDF_TOUT, OUTPUT_MARKDOWN
from kanka_knowledge.extract import extract
from kanka_knowledge.prepare import prepare
from kanka_knowledge.export import export_json, export_jsonl, export_pdf, export_markdown
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
        export_pdf(aplat_prive, OUTPUT_PDF_TOUT)
        export_markdown(aplat_prive, OUTPUT_MARKDOWN)
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
    
    # Génération automatique de la synthèse
    print(f"📝 Génération automatique de la synthèse du système...")
    try:
        generate_system_synthesis(nom_systeme)
        print(f"✅ Synthèse du système '{nom_systeme}' générée automatiquement.")
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération de synthèse : {e}")

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

def export_all_systems_with_progress(progress_callback=None):
    """
    Exporte tous les systèmes de la campagne Kanka avec suivi de progression.
    :param progress_callback: Fonction appelée pour chaque système (current, total, system_name)
    """
    from kanka_api.location import fetch_location_from_kanka
    from kanka_api.utils import kanka_api_request
    from kanka_api.config import KANKA_API_URL, CAMPAIGN_ID, HEADERS
    
    # Récupérer toutes les locations de la campagne (pagination)
    all_locations = []
    page = 1
    
    if progress_callback:
        progress_callback(0, 0, "Récupération de la liste des systèmes...")
    
    while True:
        url = f"{KANKA_API_URL}/campaigns/{CAMPAIGN_ID}/locations"
        resp = kanka_api_request('get', url, headers=HEADERS, params={"page": page})
        if resp.status_code != 200:
            raise Exception(f"Erreur récupération des locations (page {page}): {resp.status_code} {resp.text}")
        data = resp.json()
        all_locations.extend(data["data"])
        if not data.get("links", {}).get("next"):
            break
        page += 1

    # Filtrer les systèmes
    systems = [loc for loc in all_locations if loc.get("type") == "System"]
    total_systems = len(systems)
    
    if progress_callback:
        progress_callback(0, total_systems, f"{total_systems} systèmes trouvés")

    for i, system in enumerate(systems, 1):
        system_name = system.get("name", f"Système {system['id']}")
        
        if progress_callback:
            progress_callback(i, total_systems, f"Export en cours: {system_name}")
        
        try:
            system_json, system_name = fetch_location_from_kanka(system["id"])
            save_system_json(system_json, system_name)
            print(f"✅ Système '{system_name}' exporté.")
        except Exception as e:
            print(f"❌ Erreur lors de l'export de {system_name}: {e}")
            if progress_callback:
                progress_callback(i, total_systems, f"Erreur: {system_name}")
    
    if progress_callback:
        progress_callback(total_systems, total_systems, "Export terminé!")
    
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
    Enrichit un système stellaire existant en utilisant GPT-4o.
    
    Args:
        nom_systeme: Nom du système à enrichir
        prompt: Instructions d'enrichissement
        contexte: Contexte optionnel
    """
    print(f"🚀 Enrichissement du système '{nom_systeme}'...")
    
    json_path = os.path.join(GENERATED_SYSTEM_DIR, f"{nom_systeme}.json")
    agent = SWNAgent()
    
    # Charger le système existant
    with open(json_path, "r", encoding="utf-8") as f:
        original_system = json.load(f)
    
    print(f"📂 Système original chargé: {len(original_system.get('contains', []))} éléments")
    
    # Faire l'enrichissement
    enriched_system, nom = agent.enrich_system(original_system, prompt, contexte)
    
    print(f"🔍 IA a généré: {enriched_system.get('type', 'Structure')} - {enriched_system.get('name', 'Sans nom')}")
    
    # Appliquer le smart merge via l'agent
    enriched_system = agent.smart_merge(original_system, enriched_system)
    
    # Sauvegarder le système enrichi
    save_system_json(enriched_system, nom_systeme)
    print(f"✅ Système '{nom_systeme}' enrichi et sauvegardé.")
    
    # Import automatique dans Kanka
    print(f"🚀 Import automatique des nouveaux éléments dans Kanka...")
    import_system(nom_systeme)
    print(f"✅ Système '{nom_systeme}' enrichi et mis à jour dans Kanka.")
    
    # Génération automatique de la synthèse
    print(f"📝 Génération automatique de la synthèse du système...")
    try:
        generate_system_synthesis(nom_systeme)
        print(f"✅ Synthèse du système '{nom_systeme}' générée automatiquement.")
    except Exception as e:
        print(f"⚠️ Erreur lors de la génération de synthèse : {e}")

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
    
    # Auto-import des nouveaux éléments dans Kanka
    print(f"🚀 Import automatique des nouveaux éléments dans Kanka...")
    import_system(nom)
    
    print(f"✅ Structure '{nom}' enrichie, sauvegardée et importée dans Kanka.")

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


