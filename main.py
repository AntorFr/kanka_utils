import shutil
from kanka_utils.config import ZIP_PATH,OUTPUT_JSON, OUTPUT_JSON_FILTERED, OUTPUT_JSONL_TOUT, OUTPUT_JSONL_PUBLIC, OUTPUT_PDF_TOUT
from kanka_utils.extract import extract
from kanka_utils.prepare import prepare
from kanka_utils.export import export_json, export_jsonl, export_pdf
from kanka_utils.filter import filter
from kanka_utils.shape import shape
#from kanka_utils.export import sauvegarder_json, sauvegarder_jsonl

def main():
    try:
        dossier_temp, data = extract(ZIP_PATH)
        data = prepare(data)
        export_json(data,OUTPUT_JSON)
        filtered_data = filter(data)
        export_json(filtered_data,OUTPUT_JSON_FILTERED)

        

        aplat_prive, aplat_public = shape(filtered_data)
        export_jsonl(aplat_prive, OUTPUT_JSONL_TOUT)
        export_pdf(aplat_prive, OUTPUT_PDF_TOUT)

        export_jsonl(aplat_public, OUTPUT_JSONL_PUBLIC)
        
        print("✅ Export terminé.")
    finally:
        shutil.rmtree(dossier_temp)
        print("🧹 Nettoyage terminé.")

if __name__ == "__main__":
    main()