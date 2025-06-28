"""Internationalization package."""

# Re-export helper functions from the i18n module to avoid import confusion
from .. import i18n_utils as _i18n

get_translation = _i18n.get_translation
get_supported_languages = _i18n.get_supported_languages
get_language_name = _i18n.get_language_name

__all__ = ["get_translation", "get_supported_languages", "get_language_name"]
