import json
import os
import re


def load_json(file_name):
    try:
        base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, file_name)

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception as e:
        print("Błąd wczytywania:", e)
        return {}


def find_translation(word, osnova):

    w = word.lower()

    for key, value in osnova.items():

        # przypadek 1
        if key == w:
            if isinstance(value, str):
                return value

            if isinstance(value, dict):
                if "sl" in value:
                    return value["sl"]

        # przypadek 2 (lista znaczeń)
        if isinstance(value, dict):
            if "pl" in value and isinstance(value["pl"], list):
                if w in value["pl"]:
                    return key

    return None


def translate_text(text, src_lang, tgt_lang):

    if not text.strip():
        return ""

    osnova = load_json("osnova.json")

    if not osnova:
        return "Błąd: osnova.json nie została wczytana"

    tokens = re.findall(r"\w+|[^\w\s]", text, re.UNICODE)

    result = []

    for token in tokens:

        if re.match(r"[^\w\s]", token):
            result.append(token)
            continue

        translated = find_translation(token, osnova)

        if translated:

            if token[0].isupper():
                translated = translated.capitalize()

            result.append(translated)

        else:
            result.append(token)

    output = ""

    for i, token in enumerate(result):

        if i == 0:
            output += token
            continue

        if re.match(r"[.,!?;:]", token):
            output += token
        else:
            output += " " + token

    return output


def get_languages():
    return {
        "pl": "Polski",
        "sl": "Prasłowiański",
        "en": "Angielski",
        "de": "Niemiecki",
        "ru": "Rosyjski"
    }
