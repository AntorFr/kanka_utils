import openai, os
from typing import Optional
from dotenv import load_dotenv
from kanka_agent.rag_utils import load_rag_index, search_context, format_rag_context, collect_names
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

SYNTHESIS_PROMPT = """\
Tu es un expert en rédaction de synthèses pour des systèmes stellaires dans un univers de science-fiction.

Voici les données complètes d'un système stellaire :
{system_json}

Ta mission :
1. Analyser le contenu du système et ses composants
2. Rédiger une synthèse HTML concise et attrayante qui donne un aperçu général du système
3. Inclure des liens Kanka vers les éléments importants du système

IMPORTANT - Format des liens Kanka :
Pour chaque élément qui a un entity_id, utilise ce format exact :
<a href="#" class="mention" data-name="{{NOM_ELEMENT}}" data-mention="[location:{{ENTITY_ID}}]">{{NOM_ELEMENT}}</a>

Voici les éléments avec leurs entity_ids Kanka :
{elements_list}

Instructions de rédaction :
- Commence par une phrase d'introduction sur le système
- Mentionne les caractéristiques principales (étoile, planètes, stations, etc.)
- Utilise les liens Kanka pour les éléments importants
- Garde un ton immersif et professionnel
- Limite à 2-3 paragraphes maximum
- N'inclus PAS de titre <h3>, juste le contenu de la synthèse
- Évite de répéter textuellement les descriptions existantes, fais une vraie synthèse

Génère uniquement le contenu HTML de la synthèse, sans titre ni balises structurantes.
"""


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
                },
                "id":{
                    "type": "integer",
                    "description": (
                        "ID Kanka de l'élément astral. Utilisé pour les mises à jour. absent pour les nouvelles créations."
                    ),
                },
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
    },
    {
        "name": "generate_system_synthesis",
        "description": (
            "Génère une synthèse HTML concise et attrayante pour un système stellaire complet."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "synthesis": {
                    "type": "string",
                    "description": (
                        "Synthèse HTML du système stellaire. Doit inclure :\n"
                        "- Une introduction générale sur le système\n"
                        "- Les caractéristiques principales (étoile, planètes, stations, etc.)\n"
                        "- Des liens Kanka au format : <a href=\"#\" class=\"mention\" data-name=\"NOM\" data-mention=\"[location:ENTITY_ID]\">NOM</a>\n"
                        "- Un ton immersif et professionnel\n"
                        "- 2-3 paragraphes maximum\n"
                        "- PAS de titre <h3>, juste le contenu de la synthèse\n"
                        "- Éviter de répéter textuellement les descriptions existantes"
                    ),
                }
            },
            "required": ["synthesis"]
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

    def _prepare_context_and_rag(self, main_name, contexte, existing_json=None):
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
        if main_name:
            rag_passages += search_context(main_name, index, passages)
        if contexte_str.strip():
            rag_passages += search_context(contexte_str, index, passages)
        # Ajout du contexte pour les éléments contenus dans le JSON existant
        if existing_json and isinstance(existing_json, dict):
            contained_names = collect_names(existing_json)
            for name in set(contained_names):
                rag_passages += search_context(name, index, passages)
        # Supprimer les doublons éventuels
        rag_passages = [dict(t) for t in {tuple(sorted(p.items())) for p in rag_passages if isinstance(p, dict)}] if rag_passages and isinstance(rag_passages[0], dict) else list(set(rag_passages))
        rag_context_str = format_rag_context(rag_passages)

        full_context = contexte_str
        if rag_context_str:
            full_context += f"\nContexte base de connaissance :\n{rag_context_str}"
        return full_context

    def _generate_or_enrich(
        self,
        main_name: Optional[str],
        main_type: Optional[str],
        contexte: Optional[str],
        location: Optional[str],
        existing_json: Optional[dict],
        prompt: Optional[str],
        system_mode: bool = True
    ) -> tuple:
        """
        Mutualise la génération/enrichissement de système ou structure.
        :return: Tuple (json, nom_effectif)
        """
        full_context = self._prepare_context_and_rag(main_name, contexte, existing_json)

        # Construction du prompt utilisateur
        if existing_json is not None:
            enrich_text = (
                f"Voici la structure actuelle :\n{json.dumps(existing_json, ensure_ascii=False, indent=2)}\n\n"
            )
            if prompt:
                enrich_text += f"Consigne d'enrichissement :\n{prompt}\n"
            if system_mode:
                enrich_text += (
                    f"IMPORTANT : Enrichie le système stellaire '{main_name}' en PRESERVANT ABSOLUMENT tous les corps astraux existants. "
                    "RESPECTE la structure existante complète et ne modifie PAS les éléments déjà présents. "
                    "Tu peux enrichir les descriptions existantes et ajouter de nouveaux corps astraux naturels (Planète, Lune, Astéroïdes, Comète). "
                    "Pour chaque nouveau corps, donne un nom, un type, une description et des caractéristiques. "
                    "CONSERVE tous les IDs et la hiérarchie existante. Retourne le système COMPLET avec tous les éléments originaux plus les nouveaux."
                )
            else:
                enrich_text += (
                    f"IMPORTANT : Enrichie la structure artificielle '{main_name}' en PRESERVANT ABSOLUMENT tous les éléments existants. "
                    "RESPECTE la structure existante complète et ne modifie PAS les éléments déjà présents. "
                    "Tu peux enrichir les descriptions existantes et ajouter de nouveaux éléments artificiels (Station, Colonie, Ruines, Ville, Débris spaciaux). "
                    "Pour chaque nouvel élément, donne un nom, un type, une description et des caractéristiques. "
                    "CONSERVE tous les IDs et la hiérarchie existante. Retourne la structure COMPLETE avec tous les éléments originaux plus les nouveaux."
                )
            user_content = {
                "role": "user",
                "content": enrich_text
            }
        else:
            # Génération classique
            if system_mode:
                if main_name:
                    base_text = (
                        f"Crée un système stellaire nommé '{main_name}' avec tous ses corps astraux naturels "
                        "(étoile, planètes, lunes, astéroïdes, comètes). "
                        "Pour chaque corps, donne un nom, un type, une description et des caractéristiques."
                    )
                else:
                    base_text = (
                        "Crée un système stellaire original (nomme-le toi-même) avec tous ses corps astraux naturels "
                        "(étoile, planètes, lunes, astéroïdes, comètes). "
                        "Pour chaque corps, donne un nom, un type, une description et des caractéristiques."
                    )
            else:
                if main_name and main_type:
                    base_text = (
                        f"Génère une structure artificielle de type '{main_type}' nommée '{main_name}'. "
                        "Donne une description immersive et cohérente avec le contexte de l'univers. "
                        "Indique le nom de l'emplacement parent si pertinent."
                    )
                elif main_type and not main_name:
                    base_text = (
                        f"Génère une structure artificielle de type '{main_type}' et choisis un nom approprié. "
                        "Donne une description immersive et cohérente avec le contexte de l'univers. "
                        "Indique le nom de l'emplacement parent si pertinent."
                    )
                elif main_name and not main_type:
                    base_text = (
                        f"Génère une structure artificielle nommée '{main_name}' et choisis un type approprié parmi Station, Colonie, Ruines, Ville, Débris spaciaux. "
                        "Donne une description immersive et cohérente avec le contexte de l'univers. "
                        "Indique le nom de l'emplacement parent si pertinent."
                    )
                else:
                    base_text = (
                        "Génère une structure artificielle originale (nom et type à choisir) parmi Station, Colonie, Ruines, Ville, Débris spaciaux. "
                        "Donne une description immersive et cohérente avec le contexte de l'univers. "
                        "Indique le nom de l'emplacement parent si pertinent."
                    )
            user_content = {
                "role": "user",
                "content": base_text
            }

        if full_context.strip():
            user_content["content"] += f" Contexte : {full_context}"
        if location:
            user_content["content"] += f" Emplacement parent : {location}"

        function_name = "generate_astral_system" if system_mode else "generate_artifical_location"
        system_prompt = SYSTEM_PROMPT if system_mode else STRUCTURE_PROMPT

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                user_content
            ],
            functions=FUNCTIONS,
            function_call={"name": function_name}
        )

        arguments = response.choices[0].message.function_call.arguments
        try:
            result_json = json.loads(arguments)
        except Exception:
            result_json = arguments  # fallback brut si non JSON

        nom = None
        if isinstance(result_json, dict):
            nom = result_json.get("name") or main_name
        return result_json, nom

    def generate_system(self, nom_systeme: str = "", contexte: Optional[str] = None) -> tuple:
        """
        Génère un système stellaire SWN en appelant l'API GPT.
        """
        return self._generate_or_enrich(
            main_name=nom_systeme,
            main_type=None,
            contexte=contexte,
            location=None,
            existing_json=None,
            prompt=None,
            system_mode=True
        )

    def enrich_system(self, system_json: dict, prompt: str, contexte: Optional[str] = None) -> tuple:
        """
        Enrichit un système existant via GPT.
        """
        return self._generate_or_enrich(
            main_name=system_json.get("name"),
            main_type=system_json.get("type"),
            contexte=contexte,
            location=None,
            existing_json=system_json,
            prompt=prompt,
            system_mode=True
        )

    def generate_structure(self, nom_structure: str, type_structure: str, contexte: Optional[str] = None, location: Optional[str] = None) -> tuple:
        """
        Génère une structure artificielle SWN (station, colonie, ruines, ville, débris spatiaux) en appelant l'API GPT.
        """
        return self._generate_or_enrich(
            main_name=nom_structure,
            main_type=type_structure,
            contexte=contexte,
            location=location,
            existing_json=None,
            prompt=None,
            system_mode=False
        )

    def enrich_structure(self, structure_json: dict, prompt: str, contexte: Optional[str] = None, location: Optional[str] = None) -> tuple:
        """
        Enrichit une structure artificielle existante via GPT.
        """
        return self._generate_or_enrich(
            main_name=structure_json.get("name"),
            main_type=structure_json.get("type"),
            contexte=contexte,
            location=location,
            existing_json=structure_json,
            prompt=prompt,
            system_mode=False
        )
    
    def generate_system_synthesis(self, system_data: dict) -> str:
        """
        Génère une synthèse automatique du système en utilisant ChatGPT avec le système de FUNCTIONS.
        """
        if "id" not in system_data:
            raise ValueError(f"Le système '{system_data.get('name', 'inconnu')}' n'a pas d'ID Kanka.")
        
        # Extraire tous les éléments avec leurs entity_ids pour créer les liens
        def extract_elements_with_entity_ids(container, elements_list=None):
            if elements_list is None:
                elements_list = []
            
            if "contains" in container:
                for element in container["contains"]:
                    if "entity_id" in element:
                        elements_list.append({
                            "name": element["name"],
                            "type": element["type"],
                            "entity_id": element["entity_id"],
                            "entry": element.get("entry", "")
                        })
                    # Récursion pour les sous-éléments
                    extract_elements_with_entity_ids(element, elements_list)
            
            return elements_list
        
        elements = extract_elements_with_entity_ids(system_data)
        
        # Préparer les données pour le prompt
        system_json_str = json.dumps(system_data, ensure_ascii=False, indent=2)
        elements_list = "\n".join([f"- {elem['name']} (entity_id: {elem['entity_id']}) - Type: {elem['type']}" for elem in elements])
        
        # Formater le prompt avec les données
        formatted_prompt = SYNTHESIS_PROMPT.format(
            system_json=system_json_str,
            elements_list=elements_list
        )

        try:
            # Appeler l'API OpenAI avec le système de FUNCTIONS
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "Tu es un expert en rédaction de synthèses pour des univers de science-fiction. Tu produis du contenu HTML propre et professionnel."},
                    {"role": "user", "content": formatted_prompt}
                ],
                functions=FUNCTIONS,
                function_call={"name": "generate_system_synthesis"}
            )
            
            # Extraire la synthèse depuis la réponse de la fonction
            arguments = response.choices[0].message.function_call.arguments
            try:
                result_json = json.loads(arguments)
                synthesis_content = result_json.get("synthesis", "").strip()
            except Exception:
                print(f"❌ Erreur parsing JSON: {arguments}")
                return system_data.get("entry", "")
            
            # Nettoyage robuste des anciennes synthèses
            original_entry = system_data.get("entry", "")
            
            # Nettoyer toutes les synthèses existantes (multiples variantes possibles)
            patterns_to_clean = [
                "<p><span style=\"color:rgb(205,214,244);font-size:1.5rem;background-color:unset;\">Synthèse du système",  # Format Kanka avec style
                "<p><span style=\"color:rgb(205,214,244);font-size:1.5rem;\">Synthèse du système",  # Variante format Kanka
                "<h3>Synthèse du système",
                "<h2>Synthèse du système", 
                "<h4>Synthèse du système",
                "Synthèse du système",
                "<h3>Synthese du systeme",  # sans accents
                "<h2>Synthese du systeme",
                "<h4>Synthese du systeme"
            ]
            
            cleaned_entry = original_entry
            for pattern in patterns_to_clean:
                if pattern in cleaned_entry:
                    # Trouver le début de la synthèse et tout supprimer après
                    cleaned_entry = cleaned_entry.split(pattern)[0].strip()
                    print(f"🧹 Nettoyage de l'ancienne synthèse détectée avec pattern: {pattern}")
                    break
            
            original_entry = cleaned_entry
            
            # Si la nouvelle synthèse est vide, garder seulement la description originale
            if not synthesis_content:
                return original_entry
            
            # Créer la nouvelle synthèse avec titre
            synthesis_with_title = f"<h3>Synthèse du système {system_data['name']}</h3>\n{synthesis_content}"
            
            # Combiner : description originale + nouvelle synthèse (remplacement complet)
            if original_entry.strip():
                updated_entry = f"{original_entry}\n\n{synthesis_with_title}"
            else:
                # Si pas de description originale, juste la synthèse
                updated_entry = synthesis_with_title
            
            return updated_entry
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération de la synthèse : {e}")
            return system_data.get("entry", "")