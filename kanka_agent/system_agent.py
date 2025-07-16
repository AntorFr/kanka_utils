import openai, os
from typing import Optional
from dotenv import load_dotenv
from kanka_agent.rag_utils import load_rag_index, search_context, format_rag_context
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

STRUCTURE_PROMPT = """\
Tu es un assistant expert en génération d’univers de science-fiction pour des jeux de rôle spatiaux comme Stars Without Number (SWN).
Tu as accès à une base de connaissance décrivant un univers, ses civilisations, ses technologies et ses menaces.
Ta mission est de générer une structure du type demandé (Station, Colonie, Ruines, Ville, Debrits spaciaux..) immersifs et équilibrés dans ce contexte.
Tu produis toujours du JSON structuré et cohérent, adapté à une intégration dans une base de données de campagne.
la generation doit se limiter aux structures artificielles du systeme, les types possibles sont Station, Colonie, Ruines, Ville, Debrits spaciaux. les structures doivent coller au lore du monde d'Eneria
"""

# Charger les variables d'environnement depuis un fichier .env


# Fonction virtuelle déclarée à l'API GPT
FUNCTIONS = [
    {
        "name": "generate_astral_system",
        "description": (
            "Génère un système stellaire SWN basé sur la base de connaissance actuelle."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Nom de l'élément astral. Pour un système : nom du système. "
                        "Pour une planète, lune, etc., nom unique dans le système."
                    ),
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "System", "Planete", "Lune", "Asteroides", "Comete",
                        "Anomalie spatiale", "Nebuleuse"
                    ],
                    "description": (
                        "Type d'élément astral à générer. Exemples : System, Planete, Lune, "
                        "Asteroides, Comete, Anomalie spatiale, Nebuleuse. "
                        "Genre cette elements de maniere structurée pour le rendre facile a lire, "
                        "il sera importé dans kanka, le texte doit donc contenir une mise en forme html."
                    ),
                },
                "entry": {
                    "type": "string",
                    "description": (
                        "Description de l'élément astral. Pour un système, décrire le soleil, sa puissance, sa couleur, etc. "
                        "Pour une planète ou une lune : composition, géologie, atmosphère, climat, biosphère, etc. "
                        "Pour les astéroïdes, nebuleuses et comètes : composition, taille, trajectoire."
                    ),
                },
                "location": {
                    "type": "string",
                    "description": (
                        "Nom de l'emplacement parent. Vide pour les systèmes. "
                        "Pour les autres : nom du système ou de la planète parente (ex. Sorinth, Sorinth III, etc.)."
                    ),
                },
                "contains": {
                    "type": "array",
                    "description": (
                        "Liste des corps astraux contenus dans cet élément (planètes d’un système, lunes d’une planète, etc.)."
                    ),
                    "items": {
                        "$ref": "#"
                    }
                }
            },
            "required": ["name", "type", "entry"]
        }
    },
    {
        "name": "generate_artifical_location",
        "description": (
            "Génère une location artificielle SWN basée sur la base de connaissance actuelle."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Nom de l'élément, choisie des nom cohérent avec le type d'élément. "
                        "Par exemple, pour une station spatiale : 'Station Alpha', pour une colonie : "
                        "'Colonie de Nova Prime' si elle est sur Nova Prime, etc."
                    ),
                },
                "type": {
                    "type": "string",
                    "enum": [
                        "Station", "Colonie", "Ruines", "Ville",
                        "Debrits spaciaux", "anomalies spatiales"
                    ],
                    "description": (
                        "Type d'élément artificiel à générer. Exemples : Station, Colonie, Ruines, Ville, "
                        "Debrits spaciaux, Anomalies spatiales."
                    ),
                },
                "entry": {
                    "type": "string",
                    "description": (
                        "description de l'élément. Pour une station ou une colonie : sa fonction, son architecture, "
                        "son histoire, le nombre de personnes qui y vivent, les services disponibles, les factions qui la controle. "
                        "Pour des ruines : leur origine, leur état actuel, les dangers potentiels. Pour une ville : sa taille, "
                        "son organisation sociale, ses points d'intérêt, les services disponible (marchands, soins, reparation). "
                        "Pour des débris spatiaux : leur origine, leur composition, les dangers associés. "
                        "Genre cette elements de maniere structurée pour le rendre facile a lire, il sera importé dans kanka, "
                        "le texte doit donc contenir une mise en forme html"
                    ),
                },
                "location": {
                    "type": "string",
                    "description": (
                        "le nom de l'emplacement parent. lune, planete, systeme pour les stations ou debrits spaciaux. "
                        "Planete ou lune pour les colonies, villes. n'importe le quel pour les ruines."
                    ),
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
                    "(étoile, planètes, lunes, astéroïdes, comètes). "
                    "Pour chaque corps, donne un nom, un type, une description et des caractéristiques."
                )
            }
        else:
            user_content = {
                "role": "user",
                "content": (
                    "Crée un système stellaire original (nomme-le toi-même) avec tous ses corps astraux naturels "
                    "(étoile, planètes, lunes, astéroïdes, comètes). "
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
            function_call={"name": "generate_astral_system"}
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


    def generate_structure(self, nom_structure: str, type_structure: str, contexte: Optional[str] = None, location: Optional[str] = None) -> tuple:
        """
        Génère une structure artificielle SWN (station, colonie, ruines, ville, débris spatiaux) en appelant l'API GPT.

        :param nom_structure: Nom de la structure à générer
        :param type_structure: Type de la structure (Station, Colonie, Ruines, Ville, Debrits spaciaux)
        :param contexte: Optionnel, texte de background/context
        :param location: Optionnel, nom de l'emplacement parent (planète, lune, système, etc.)
        :return: Tuple (structure_json, nom_structure_effectif)
        """
        # Correction : accepte str ou list[str] pour contexte
        if isinstance(contexte, list):
            contexte_str = " ".join(str(x) for x in contexte)
        elif contexte is not None:
            contexte_str = str(contexte)
        else:
            contexte_str = ""

        # Ajout du contexte RAG
        index, passages = load_rag_index()
        rag_passages = []
        if nom_structure:
            rag_passages += search_context(nom_structure, index, passages)
        if contexte_str.strip():
            rag_passages += search_context(contexte_str, index, passages)
        # Supprimer les doublons éventuels
        rag_passages = [dict(t) for t in {tuple(sorted(p.items())) for p in rag_passages if isinstance(p, dict)}] if rag_passages and isinstance(rag_passages[0], dict) else list(set(rag_passages))
        rag_context_str = format_rag_context(rag_passages)

        full_context = contexte_str
        if rag_context_str:
            full_context += f"\nContexte base de connaissance :\n{rag_context_str}"


        if nom_structure and type_structure:
            user_content = {
            "role": "user",
            "content": (
                f"Génère une structure artificielle de type '{type_structure}' nommée '{nom_structure}'. "
                "Donne une description immersive et cohérente avec le contexte de l'univers. "
                "Indique le nom de l'emplacement parent si pertinent."
            )
            }
        elif type_structure and not nom_structure:
            user_content = {
            "role": "user",
            "content": (
                f"Génère une structure artificielle de type '{type_structure}' et choisis un nom approprié. "
                "Donne une description immersive et cohérente avec le contexte de l'univers. "
                "Indique le nom de l'emplacement parent si pertinent."
            )
            }
        elif nom_structure and not type_structure:
            user_content = {
            "role": "user",
            "content": (
                f"Génère une structure artificielle nommée '{nom_structure}' et choisis un type approprié parmi Station, Colonie, Ruines, Ville, Débris spaciaux. "
                "Donne une description immersive et cohérente avec le contexte de l'univers. "
                "Indique le nom de l'emplacement parent si pertinent."
            )
            }
        else:
            user_content = {
            "role": "user",
            "content": (
                "Génère une structure artificielle originale (nom et type à choisir) parmi Station, Colonie, Ruines, Ville, Débris spaciaux. "
                "Donne une description immersive et cohérente avec le contexte de l'univers. "
                "Indique le nom de l'emplacement parent si pertinent."
            )
            }

        if full_context.strip():
            user_content["content"] += f" Contexte : {full_context}"
        if location:
            user_content["content"] += f" Emplacement parent : {location}"

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": STRUCTURE_PROMPT},
                user_content
            ],
            functions=FUNCTIONS,
            function_call={"name": "generate_artifical_location"}
        )

        arguments = response.choices[0].message.function_call.arguments
        try:
            structure = json.loads(arguments)
        except Exception:
            structure = arguments  # fallback brut si non JSON

        nom = None
        if isinstance(structure, dict):
            nom = structure.get("name") or nom_structure
        return structure, nom