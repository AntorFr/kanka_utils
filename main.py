import shutil
from kanka_knowledge.config import ZIP_PATH,OUTPUT_JSON, OUTPUT_JSON_FILTERED, OUTPUT_JSONL_TOUT, OUTPUT_JSONL_PUBLIC, OUTPUT_PDF_TOUT
from kanka_knowledge.extract import extract
from kanka_knowledge.prepare import prepare
from kanka_knowledge.export import export_json, export_jsonl, export_pdf
from kanka_knowledge.filter import filter
from kanka_knowledge.shape import shape

from kanka_agent.rag_utils import create_rag_index
from kanka_agent.system_agent import SWNAgent

from kanka_api.import_location import import_system_from_file, import_location_tree, fetch_location_from_kanka
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
        #agent = SWNAgent()
        #nom_systeme = "Ravenis"
        #contexte = [
        #        "Alimenté par Rav, une géante rouge en fin de vie, il se situe hors des routes de saut officielles. L’instabilité de son rayonnement masque efficacement les signatures énergétiques.",
        #        "Ravenis I : planète tellurique stérile, sert de terrain d’entraînement et de dépôt d’armement."
        #        "Ravenis II : vaste géante gazeuse",
        #        "Nebrax, une lune de Ravenis II",
        #        "Ceinture de Vol-Ruun : "]
       # 
       # systeme, nom_systeme = agent.generate_system(nom_systeme, contexte)
        #import_location_tree(systeme)
        #save_system_json(systeme, nom_systeme)

        #nom_structure = ""
        #contexte = ["Crée moi une station en orbite de Vortexis III, commander par les pirates du soleil noir, qui sert de base logistique pour les raids dans les secteurs de l'AST mais aussi de marche noir ou l'on y trouve de tout a tout les prix. elle est egalement la pour proteger Habre des lames, la ville Pirate sur la planette QG de l'organisation. La station doit être capable de réparer les vaisseaux, stocker des ressources. Elle doit également avoir une salle de commandement avec une vue sur la planète et un hangar pour les vaisseaux."]
        #structure, nom = agent.generate_structure("",type_structure="Colonies", contexte=contexte,location="Vortexis III")
        #save_system_json(structure, nom)
        #import_location_tree(structure)

        systeme, nom = fetch_location_from_kanka(1757374)
        save_system_json(systeme, nom)

if __name__ == "__main__":
    main()
    #import_system_from_file("generated_systems/Sol.json")


