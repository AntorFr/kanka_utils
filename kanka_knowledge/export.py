import json, re
from fpdf import FPDF

def export_json(data, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def export_jsonl(lignes, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        for ligne in lignes:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")

def export_markdown(lignes, chemin):
    """
    Exporte les données de la base de connaissance en format Markdown optimisé pour les GPT.
    """
    with open(chemin, "w", encoding="utf-8") as f:
        f.write("# Base de Connaissance - Univers d'Eneria\n\n")
        f.write("*Base de données complète pour la génération de contenu IA dans l'univers d'Eneria*\n\n")
        f.write("---\n\n")
        
        # Grouper par type pour une meilleure organisation
        types_groups = {}
        for ligne in lignes:
            type_element = ligne.get("type", "Divers")
            if type_element not in types_groups:
                types_groups[type_element] = []
            types_groups[type_element].append(ligne)
        
        # Ordre préféré pour l'affichage
        ordre_types = [
            "System", "Planete", "Lune", "Asteroides", "Station", "Colonie", 
            "Organisation", "Faction", "Personnage", "Technologie", "Vaisseau",
            "Artefact", "Lieu", "Evenement", "Divers"
        ]
        
        # Ajouter tous les autres types non listés
        for type_element in types_groups.keys():
            if type_element not in ordre_types:
                ordre_types.append(type_element)
        
        for type_element in ordre_types:
            if type_element not in types_groups:
                continue
                
            elements = types_groups[type_element]
            if not elements:
                continue
                
            f.write(f"## {type_element}\n\n")
            
            for ligne in elements:
                titre = ligne.get("titre", "Sans titre")
                contenu = ligne.get("contenu", {})
                
                f.write(f"### {titre}\n\n")
                
                if isinstance(contenu, str):
                    # Nettoyer le HTML basique et convertir en Markdown
                    contenu_clean = clean_html_to_markdown(contenu)
                    f.write(f"{contenu_clean}\n\n")
                    
                elif isinstance(contenu, dict):
                    # Contenu structuré
                    if "entry" in contenu:
                        entry_clean = clean_html_to_markdown(contenu["entry"])
                        f.write(f"{entry_clean}\n\n")
                    
                    # Ajouter d'autres champs pertinents
                    for key, value in contenu.items():
                        if key != "entry" and value and isinstance(value, str):
                            f.write(f"**{key.title()}**: {clean_html_to_markdown(value)}\n\n")
                            
                elif isinstance(contenu, list):
                    # Liste d'éléments
                    for entry in contenu:
                        if isinstance(entry, dict):
                            name = entry.get("name", "Sans nom")
                            entry_text = entry.get("entry", "")
                            f.write(f"#### {name}\n\n")
                            if entry_text:
                                entry_clean = clean_html_to_markdown(entry_text)
                                f.write(f"{entry_clean}\n\n")
                
                f.write("---\n\n")
    
    print(f"✅ Base de connaissance exportée en Markdown vers : {chemin}")

def clean_html_to_markdown(text: str) -> str:
    """
    Convertit le HTML basique en Markdown et nettoie le texte.
    """
    if not isinstance(text, str):
        return ""
    
    # Remplacer les balises HTML courantes par du Markdown
    text = re.sub(r'<h([1-6])>(.*?)</h[1-6]>', r'#\1 \2', text)  # Titres
    text = re.sub(r'<strong>(.*?)</strong>', r'**\1**', text)  # Gras
    text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)  # Gras
    text = re.sub(r'<em>(.*?)</em>', r'*\1*', text)  # Italique
    text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)  # Italique
    text = re.sub(r'<p>(.*?)</p>', r'\1\n\n', text)  # Paragraphes
    text = re.sub(r'<br\s*/?>', '\n', text)  # Retours à la ligne
    text = re.sub(r'<ul>(.*?)</ul>', r'\1', text, flags=re.DOTALL)  # Listes
    text = re.sub(r'<li>(.*?)</li>', r'- \1\n', text)  # Items de liste
    
    # Nettoyer les liens Kanka (garder le texte mais enlever les balises)
    text = re.sub(r'<a[^>]*>(.*?)</a>', r'\1', text)
    
    # Supprimer les autres balises HTML
    text = re.sub(r'<[^>]+>', '', text)
    
    # Nettoyer les espaces multiples et caractères spéciaux
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('\xa0', ' ')  # Espaces insécables
    
    # Nettoyer les retours à la ligne multiples
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    return text.strip()



class KnowledgePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("DejaVu", "", "./fonts/DejaVuSans.ttf", uni=True)
        self.add_font("DejaVu", "B", "./fonts/DejaVuSans-Bold.ttf", uni=True)
        self.set_font("DejaVu", "", 11)

    def header(self):
        self.set_font("DejaVu", "", 14)
        self.cell(0, 10, "Base de Connaissance - Export PDF", border=False, ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("DejaVu", "B", 12)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 10, safe_text(title), ln=True, fill=True)
        self.ln(2)

    def chapter_entry(self, name, text):
        width = self.w - self.l_margin - self.r_margin

        self.set_font("DejaVu", "B", 11)
        self.set_x(self.l_margin)
        try:
            self.multi_cell(width, 8, safe_text(name))
        except Exception as e:
            print("💥 Erreur dans le nom :", name)
            raise e

        self.set_font("DejaVu", "", 11)
        self.set_x(self.l_margin)
        try:
            if not text or not isinstance(text, str):
                return
            self.multi_cell(width, 8, safe_text(text))
        except Exception as e:
            print("💥 Erreur dans le contenu de l'entrée :")
            print(text[:300])
            raise e

        self.ln(4)


def clean_text(text: str) -> str:
    """Nettoie les caractères invisibles, insécables, etc."""
    if not isinstance(text, str):
        return ""
    text = text.replace("\xa0", " ")
    text = text.replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def break_long_segments(text: str, max_len: int = 80) -> str:
    """Coupe tous les mots de plus de `max_len` caractères avec un retour à la ligne forcé."""
    def breaker(match):
        word = match.group(0)
        return '\n'.join([word[i:i + max_len] for i in range(0, len(word), max_len)])
    return re.sub(rf'\S{{{max_len},}}', breaker, text)

def safe_text(text: str) -> str:
    """Combine le nettoyage général et le découpage de mots longs."""
    return break_long_segments(clean_text(text))

def export_pdf(lignes, chemin):
    pdf = KnowledgePDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    for ligne in lignes:
        if ligne.get("type") == "Liaison FTL":
            continue

        type_ = ligne.get("type", "inconnu")
        titre = ligne.get("titre", "Sans titre")

        titre_complet = f"{type_} : {titre}"
        contenu = ligne.get("contenu", {})

        pdf.chapter_title(titre_complet)

        if isinstance(contenu, str):
            pdf.chapter_entry("", contenu)
        elif isinstance(contenu, list):
            for entry in contenu:
                name = entry.get("name", "Sans nom")
                entry_text = entry.get("entry", "")
                pdf.chapter_entry(name, entry_text)

    pdf.output(chemin)
    print(f"✅ PDF exporté avec succès vers : {chemin}")
