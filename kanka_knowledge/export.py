import json, re
from fpdf import FPDF

def export_json(data, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def export_jsonl(lignes, chemin):
    with open(chemin, "w", encoding="utf-8") as f:
        for ligne in lignes:
            f.write(json.dumps(ligne, ensure_ascii=False) + "\n")



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
