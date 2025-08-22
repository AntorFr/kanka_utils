"""
Configuration pour le module kanka_image
"""

# Paramètres par défaut de compression
DEFAULT_SCALE_FACTOR = 0.5  # 50% de la taille originale
DEFAULT_PALETTE_SIZE = 256  # Maximum de couleurs
DEFAULT_QUALITY = 85  # Qualité de compression

# Extensions de fichiers supportées
SUPPORTED_FORMATS = ['.png', '.PNG']

# Paramètres de compression avancée
COMPRESSION_SETTINGS = {
    'optimize': True,
    'compress_level': 9,  # Compression maximale pour PNG
}

# Dossiers par défaut
DEFAULT_INPUT_DIR = "images"
DEFAULT_OUTPUT_DIR = "images/compressed"

# Logging
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
