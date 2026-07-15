from src.i18n.en import TRANSLATIONS as EN_TRANSLATIONS
from src.i18n.zh import TRANSLATIONS as ZH_TRANSLATIONS


TRANSLATIONS = {
    "zh": ZH_TRANSLATIONS,
    "en": EN_TRANSLATIONS,
}


def t(key, language="zh"):
    translations = TRANSLATIONS.get(language, ZH_TRANSLATIONS)
    return translations.get(key, key)
