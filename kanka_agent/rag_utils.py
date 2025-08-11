import faiss
import numpy as np
import json, os
import openai
import textwrap
from dotenv import load_dotenv
from tqdm import tqdm


load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

EMBEDDING_MODEL = "text-embedding-3-large" #"text-embedding-3-small"

MAX_CHARS = 2000  # Limite stricte avant envoi à l'embedding API

def load_chunks(jsonl_path):
    with open(jsonl_path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f]

    passages = []
    for obj in lines:
        titre = obj.get("titre", "Sans titre")
        contenu = obj.get("contenu", "")
        if isinstance(contenu, list):
            for e in contenu:
                texte = e.get("entry", "")
                wrapped = textwrap.wrap(texte, width=MAX_CHARS)
                passages.extend([f"{titre} - {e.get('name', '')} : {chunk}" for chunk in wrapped])
        elif isinstance(contenu, str):
            wrapped = textwrap.wrap(contenu, width=MAX_CHARS)
            passages.extend([f"{titre} : {chunk}" for chunk in wrapped])
    return passages

def embed_texts(texts):
    vectors = []
    for i in tqdm(range(0, len(texts), 100), desc="Embedding"):
        batch = texts[i:i+100]
        batch = [t[:MAX_CHARS] for t in batch]  # Troncature de sécurité
        resp = openai.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch
        )
        vectors.extend([v.embedding for v in resp.data])
    return vectors

def build_faiss_index(passages, vectors):
    dim = len(vectors[0])
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(vectors).astype("float32"))
    return index

def save_index(index, passages, path="rag_index"):
    faiss.write_index(index, f"{path}.index")
    with open(f"{path}.json", "w", encoding="utf-8") as f:
        json.dump(passages, f, ensure_ascii=False)

def load_rag_index(path="rag_index"):
    index = faiss.read_index(f"{path}.index")
    with open(f"{path}.json", "r", encoding="utf-8") as f:
        passages = json.load(f)
    return index, passages

def search_context(query: str, index, passages, top_k=5):
    embedding = openai.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query
    ).data[0].embedding

    D, I = index.search(np.array([embedding]).astype("float32"), top_k)
    return [passages[i] for i in I[0]]

def create_rag_index(jsonl_path, output="rag_index"):
    passages = load_chunks(jsonl_path)
    vectors = embed_texts(passages)
    index = build_faiss_index(passages, vectors)
    save_index(index, passages, path=output)

def format_rag_context(passages: list) -> str:
    """
    Formate les passages RAG enrichis pour affichage dans le prompt.
    """
    context_lines = []
    for p in passages:
        if isinstance(p, dict):
            line = p.get("text", str(p))
            if "type" in p:
                line += f" [type: {p['type']}]"
            if "tags" in p and p["tags"]:
                line += f" [tags: {', '.join(p['tags'])}]"
            if "links" in p and p["links"]:
                line += f" [liens: {', '.join(p['links'])}]"
            context_lines.append(line)
        else:
            context_lines.append(str(p))
    return "\n".join(context_lines)

def collect_names(obj):
    names = []
    if isinstance(obj, dict):
        if "name" in obj and obj["name"]:
            names.append(obj["name"])
        if "contains" in obj and isinstance(obj["contains"], list):
            for item in obj["contains"]:
                names.extend(collect_names(item))
    elif isinstance(obj, list):
        for item in obj:
            names.extend(collect_names(item))
    return names 