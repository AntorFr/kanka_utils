# --- Configuration ---
import os
from dotenv import load_dotenv

KANKA_API_URL = "https://api.kanka.io/1.0"
CAMPAIGN_ID = "326335"  # Remplace par l'id de ta campagne

load_dotenv()
KANKA_TOKEN = os.getenv("KANKA_TOKEN")  # Assure-toi que .env contient KANKA_TOKEN=ton_token


HEADERS = {
    "Authorization": f"Bearer {KANKA_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

ICONS_LOCATIONS = {
    "Anomalie spatiale":"9f582c75-13ff-440b-b492-0f2c6b30d203",
    "Asteroides":"9f49d4fd-eb20-4c54-a947-773d9568c051",
    "Planete":"9f3ba072-7d9f-484b-aa17-11abd968962c",
    "Lune":"9f484908-d85b-4194-a99e-3f376816256f",
    "System":"9f3a05bf-ca51-4507-961a-1b638e5ffa5a",
    "Station":"9f3ba543-16c0-4a76-bfa9-e0f3b15d1cd1",
    "Colonie":"9f484763-204d-4177-a9e8-bbf5bb911165",
    "Ruines":"9f583922-e0ab-416d-bd1b-691b1ed9f58e",
    "Comete":"9f583964-7c5a-4134-98f6-c1e191487653",
    "Nebuleuse":"9f583922-be59-4041-a9e9-f140a15f570d",
}