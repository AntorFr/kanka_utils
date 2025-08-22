# Module de gestion et compression d'images pour Kanka
# Outils pour optimiser les images d'illustration des campagnes

from .compress import (
    ImageCompressor,
    compress_folder_smart,
    smart_compress_folder,
    compress_png,
    batch_compress_images,
    create_round_token,
    smart_create_tokens
)
from .streamlit_utils import (
    streamlit_image_compression_page,
    streamlit_compression_settings,
    streamlit_compress_images,
    streamlit_display_results
)

__all__ = [
    'compress_png', 
    'batch_compress_images', 
    'compress_folder_smart',
    'ImageCompressor',
    'create_round_token',
    'smart_create_tokens',
    'streamlit_image_compression_page',
    'streamlit_compression_settings',
    'streamlit_compress_images',
    'streamlit_display_results'
]
