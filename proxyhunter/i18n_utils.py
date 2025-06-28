"""Internationalization (i18n) support for ProxyHunter."""

import json
import os
from pathlib import Path
from typing import Dict, Any


class I18nManager:
    """Manages internationalization for ProxyHunter."""

    def __init__(self):
        self.translations = {}
        self.default_lang = "en"
        self.supported_languages = ["en", "zh", "ja"]
        self._load_translations()

    def _load_translations(self):
        """Load all translation files."""
        i18n_dir = Path(__file__).parent / "i18n"

        for lang in self.supported_languages:
            lang_file = i18n_dir / f"{lang}.json"
            try:
                with open(lang_file, "r", encoding="utf-8") as f:
                    self.translations[lang] = json.load(f)
            except FileNotFoundError:
                print(f"Warning: Translation file not found: {lang_file}")
                if lang == self.default_lang:
                    # Fallback translations for English
                    self.translations[lang] = {
                        "title": "Proxy Hunter Dashboard",
                        "language": "Language",
                        "refresh": "Refresh",
                        "proxy": "Proxy",
                        "status": "Status",
                        "response_time": "Response Time (s)",
                        "data_size": "Data Size (bytes)",
                        "total": "Total",
                        "success": "Success",
                        "fail": "Failed",
                        "average": "Average Response Time",
                        "working": "Working",
                        "failed": "Failed",
                        "proxy_list": "Proxy List",
                    }
            except json.JSONDecodeError as e:
                print(f"Error loading translation file {lang_file}: {e}")

    def get_translation(self, lang: str) -> Dict[str, str]:
        """Get translation dictionary for the specified language."""
        if lang not in self.translations:
            lang = self.default_lang
        return self.translations.get(lang, self.translations[self.default_lang])

    def get_supported_languages(self) -> list:
        """Get list of supported languages."""
        return self.supported_languages.copy()

    def get_language_name(self, lang_code: str) -> str:
        """Get display name for language code."""
        lang_names = {"en": "English", "zh": "繁體中文", "ja": "日本語"}
        return lang_names.get(lang_code, lang_code)


# Global i18n manager instance
i18n_manager = I18nManager()


def get_translation(lang: str = "en") -> Dict[str, str]:
    """Get translation dictionary for the specified language."""
    return i18n_manager.get_translation(lang)


def get_supported_languages() -> list:
    """Get list of supported languages."""
    return i18n_manager.get_supported_languages()


def get_language_name(lang_code: str) -> str:
    """Get display name for language code."""
    return i18n_manager.get_language_name(lang_code)
