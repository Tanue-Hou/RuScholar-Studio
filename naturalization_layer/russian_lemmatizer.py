import re
import pymorphy3

_morph = None

def get_morph_analyzer():
    global _morph
    if _morph is None:
        _morph = pymorphy3.MorphAnalyzer()
    return _morph

def lemmatize_word(word: str) -> str:
    """
    Lemmatize a single Russian word using pymorphy3.
    """
    if not word:
        return ""
    morph = get_morph_analyzer()
    parsed = morph.parse(word)
    if parsed:
        return parsed[0].normal_form
    return word.lower()

# Regex to match Cyrillic words
CYRILLIC_WORD_RE = re.compile(r'[а-яА-ЯёЁ]+')

def lemmatize_sentence(text: str) -> str:
    """
    Analyze Russian text and replace all Cyrillic words with their base/normal form.
    Non-Cyrillic words and punctuation are preserved.
    """
    if not text:
        return ""
        
    def replace_match(match):
        word = match.group(0)
        return lemmatize_word(word)
        
    # Lowercase first to assist dictionary match, though pymorphy handles case, lowercasing is safer
    text_lower = text.lower()
    return CYRILLIC_WORD_RE.sub(replace_match, text_lower)
