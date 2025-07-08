import shutil
from kanka_knowledge.config import ZIP_PATH,OUTPUT_JSON, OUTPUT_JSON_FILTERED, OUTPUT_JSONL_TOUT, OUTPUT_JSONL_PUBLIC, OUTPUT_PDF_TOUT
from kanka_knowledge.extract import extract
from kanka_knowledge.prepare import prepare
from kanka_knowledge.export import export_json, export_jsonl, export_pdf
from kanka_knowledge.filter import filter
from kanka_knowledge.shape import shape

from kanka_agent.rag_utils import create_rag_index
from kanka_agent.system_agent import SWNAgent

from kanka_api.import_location import import_system_from_file
from kanka_api.utils import main as kanka_api_main

from kanka_agent.export import save_system_json



#from kanka_knowledge.export import sauvegarder_json, sauvegarder_jsonl

def main():
    if False:
        try:
            dossier_temp, data = extract(ZIP_PATH)
            data = prepare(data)
            export_json(data,OUTPUT_JSON)
            filtered_data = filter(data)
            export_json(filtered_data,OUTPUT_JSON_FILTERED)

            

            aplat_prive, aplat_public = shape(filtered_data)
            export_jsonl(aplat_prive, OUTPUT_JSONL_TOUT)
            #export_pdf(aplat_prive, OUTPUT_PDF_TOUT)
            create_rag_index(OUTPUT_JSONL_TOUT) 

            export_jsonl(aplat_public, OUTPUT_JSONL_PUBLIC)
            
            print("✅ Export terminé.")
        finally:
            shutil.rmtree(dossier_temp)
            print("🧹 Nettoyage terminé.")

    else:
        # Exemple d'utilisation de l'agent
        agent = SWNAgent()
        nom_systeme = ""
        contexte = [""]
        
        systeme, nom_systeme = agent.generate_system(nom_systeme, contexte)

        # Enregistre le système généré dans un fichier JSON dans le dossier configuré
        save_system_json(systeme, nom_systeme)

if __name__ == "__main__":
    #main()
    import_system_from_file("generated_systems/Zantaray.json")


