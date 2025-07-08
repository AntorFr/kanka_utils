import openai, os
from typing import Optional
from dotenv import load_dotenv
from kanka_agent.rag_utils import load_rag_index, search_context
import json


# Prompt système pour guider le modèle
SYSTEM_PROMPT = """\
Tu es un assistant expert en génération d’univers de science-fiction pour des jeux de rôle spatiaux comme Stars Without Number (SWN).
Tu as accès à une base de connaissance décrivant un univers, ses civilisations, ses technologies et ses menaces.
Ta mission est de générer des systèmes stellaires compatibles, immersifs et équilibrés dans ce contexte.
Tu produis toujours du JSON structuré et cohérent, adapté à une intégration dans une base de données de campagne.
la generation doit se limiter au elements astraux naturel du systeme, les types possibles sont Soleil, Planète, Lune, Astéroïde, Comète, annomalie spaciale.
Pour chaque element fournis un nom, un type, une description et des caractéristiques (taille, distance, etc.) si applicable.
Essaie de respecter les conventions de nommage (nom du soleil est le nom du system, le nom des planètes composée du nom du soleil avec le numero d'ordre a l'exception tres rare de plannete particulements speciales) 
Garde des relations logiques entre les éléments (par exemple, une planète doit orbiter autour d'une étoile).
definie aleratoirement le nombre et le sortes des éléments astraux, mais assure-toi qu'ils soient cohérents et variés et coerents avec ce qu'on observe dans le cosmos reel.
"""

# Charger les variables d'environnement depuis un fichier .env


# Fonction virtuelle déclarée à l'API GPT
FUNCTIONS = [
    {
        "name": "generate_swn_system",
        "description": "Génère un système stellaire SWN basé sur la base de connaissance actuelle.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nom de l'élément astral. Pour un système : nom du système. Pour une planète, lune, etc., nom unique dans le système."
                },
                "type": {
                    "type": "string",
                    "enum": ["System", "Planete", "Lune", "Asteroides", "Comete", "Anomalie spatiale","Nebuleuse"],
                    "description": "Type d'élément astral à générer. Exemples : System, Planete, Lune, Asteroides, Comete, Anomalie spatiale, Nebuleuse."
                },
                "entry": {
                    "type": "string",
                    "description": "Description de l'élément astral. Pour un système, décrire le soleil, sa puissance, sa couleur, etc. Pour une planète ou une lune : composition, géologie, atmosphère, climat, biosphère, etc. Pour les astéroïdes, nebuleuses et comètes : composition, taille, trajectoire. Pour les anomalies : nature, effet, origine."
                },
                "location": {
                    "type": "string",
                    "description": "Nom de l'emplacement parent. Vide pour les systèmes. Pour les autres : nom du système ou de la planète parente (ex. Sorinth, Sorinth III, etc.)."
                },
                "contains": {
                    "type": "array",
                    "description": "Liste des corps astraux contenus dans cet élément (planètes d’un système, lunes d’une planète, etc.).",
                    "items": {
                        "$ref": "#"
                    }
                }
            },
            "required": ["name", "type", "entry"]
        }
    }
]

class SWNAgent:
    def __init__(self):
        """Initialise l'agent GPT avec ta clé API OpenAI."""
        load_dotenv()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

        if not OPENAI_API_KEY:
            raise ValueError("La clé OPENAI_API_KEY est manquante. Ajoutez-la dans un fichier .env à la racine du projet.")

        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)

    def generate_system(self, nom_systeme: str, contexte: Optional[str] = None):
        """
        Génère un système stellaire SWN en appelant l'API GPT.

        :param nom_systeme: Nom du système à générer
        :param contexte: Optionnel, texte de background (factions locales, lieux, etc.)
        :return: Tuple (systeme_json, nom_systeme_effectif)
        """

        #index, passages = load_rag_index()
        #contexte = search_context(nom_systeme, index, passages)

        if nom_systeme:
            user_content = {
                "role": "user",
                "content": (
                    f"Crée un système stellaire nommé '{nom_systeme}' avec tous ses corps astraux naturels "
                    "(étoile, planètes, lunes, astéroïdes, comètes, anomalies spatiales). "
                    "Pour chaque corps, donne un nom, un type, une description et des caractéristiques."
                )
            }
        else:
            user_content = {
                "role": "user",
                "content": (
                    "Crée un système stellaire original (nomme-le toi-même) avec tous ses corps astraux naturels "
                    "(étoile, planètes, lunes, astéroïdes, comètes, anomalies spatiales). "
                    "Pour chaque corps, donne un nom, un type, une description et des caractéristiques."
                )
            }
        if contexte:
            user_content["content"] += f" Contexte : {contexte}"

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                user_content
            ],
            functions=FUNCTIONS,
            function_call={"name": "generate_swn_system"}
        )

        # Récupération et parsing des arguments JSON de la réponse
        arguments = response.choices[0].message.function_call.arguments
        try:
            systeme = json.loads(arguments)
        except Exception:
            systeme = arguments  # fallback brut si non JSON

        # Récupération du nom du système (clé "name" ou "nom_systeme" selon la structure)
        nom = None
        if isinstance(systeme, dict):
            nom = systeme.get("name") or nom_systeme
        return systeme, nom
