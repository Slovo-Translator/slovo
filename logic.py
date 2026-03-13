import json
import os
import re

def load_json(file_name):
    """Bezpieczne wczytywanie JSON z gwarancją zwrotu słownika."""
    try:
        # Ustalenie ścieżki bezwzględnej do folderu ze skryptem
        base_path = os.path.dirname(os.path.abspath(__file__))
        full_path = os.path.join(base_path, file_name)
        
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        return {}
    except Exception:
        return {}

def translate_text(text, src_lang, tgt_lang):
    if not text or not text.strip():
        return ""

    # Wczytanie baz - gwarantowane słowniki
    osnova = load_json('osnova.json')
    vuzor = load_json('vuzor.json')

    if tgt_lang == "sl":
        if not osnova:
            return "Błąd: Nie wczytano bazy osnova.json. Sprawdź pliki w repozytorium."

        # Rozbijanie na słowa i znaki interpunkcyjne
        tokens = re.findall(r"[\w']+|[.,!?;]", text)
        translated_result = []

        for token in tokens:
            if token in ".,!?;":
                translated_result.append(token)
                continue

            lower_token = token.lower()
            # Szukanie w słowniku
            replacement = osnova.get(lower_token)

            if replacement:
                # Zachowanie wielkości liter
                if token[0].isupper():
                    replacement = replacement.capitalize()
                translated_result.append(replacement)
            else:
                # Jeśli nie ma w bazie, zostawiamy oryginał
                translated_result.append(token)

        # Składanie tekstu i naprawa spacji przed interpunkcją
        output = " ".join(translated_result)
        for char in ".,!?;":
            output = output.replace(f" {char}", char)
        
        return output

    return "Tłumaczenie dostępne obecnie tylko na Prasłowiański."

def get_languages():
    return {
        "pl": "Polski",
        "sl": "Prasłowiański",
        "en": "Angielski",
        "de": "Niemiecki",
        "ru": "Rosyjski"
    }
