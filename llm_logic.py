import json
import os
from collections import defaultdict, Counter

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data, file):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ========================
# 🔍 ANALIZA vuzor.json
# ========================

def detect_case(tag):
    tag = tag.lower()
    if "nominative" in tag: return "nom"
    if "genitive" in tag: return "gen"
    if "accusative" in tag: return "acc"
    if "locative" in tag: return "loc"
    if "dative" in tag: return "dat"
    if "instrumental" in tag: return "ins"
    if "vocative" in tag: return "voc"
    return "nom"

def detect_number(tag):
    return "pl" if "plural" in tag else "sg"

def extract_lemma(tag, fallback):
    if '"' in tag:
        return tag.split('"')[1]
    return fallback

def longest_common_prefix(words):
    if not words:
        return ""
    prefix = words[0]
    for w in words[1:]:
        i = 0
        while i < len(prefix) and i < len(w) and prefix[i] == w[i]:
            i += 1
        prefix = prefix[:i]
    return prefix

# ========================
# 🧠 UCZENIE WZORCÓW
# ========================

def build_models():
    vuzor = load_data("vuzor.json")

    lemmas = defaultdict(list)

    for e in vuzor:
        slov = e.get("slovian", "")
        pol = e.get("polish", "").lower()
        tag = e.get("type and case", "")

        if not slov or not pol:
            continue

        lemma = extract_lemma(tag, slov)

        lemmas[lemma].append({
            "slov": slov,
            "pol": pol,
            "case": detect_case(tag),
            "num": detect_number(tag)
        })

    grammar = {}
    polish_map = defaultdict(list)

    for lemma, forms in lemmas.items():
        slov_forms = [f["slov"] for f in forms]
        stem = longest_common_prefix(slov_forms)

        g = {}

        for f in forms:
            key = f"{f['num']}_{f['case']}"
            suffix = f["slov"][len(stem):]
            g[key] = suffix

            # 🔥 uczymy się mapowania PL → przypadek
            polish_map[f["pol"]].append(key)

        grammar[lemma] = {
            "stem": stem,
            "endings": g
        }

    # 🔥 rozstrzygamy konflikty PL → przypadek
    polish_case_map = {}
    for pol_form, keys in polish_map.items():
        most_common = Counter(keys).most_common(1)[0][0]
        polish_case_map[pol_form] = most_common

    return grammar, polish_case_map

# ========================
# 🔁 TŁUMACZENIE
# ========================

def translate(polish_word):
    grammar, polish_case_map = build_models()

    # 1. znajdź przypadek dokładnie z danych
    case_key = polish_case_map.get(polish_word)

    # 2. jeśli nie ma — spróbuj dopasować końcówkę NA PODSTAWIE DANYCH
    if not case_key:
        for pol_form, key in polish_case_map.items():
            if polish_word.endswith(pol_form[-3:]):
                case_key = key
                break

    if not case_key:
        return polish_word  # brak danych → nie zgadujemy

    # 3. znajdź lemma po podobieństwie (rdzeń PL)
    for lemma, data in grammar.items():
        stem = data["stem"]
        endings = data["endings"]

        if case_key in endings:
            # 🔥 tu NIE zgadujemy — bierzemy dokładny wzorzec
            return stem + endings[case_key]

    return polish_word

# ========================
# 🚀 TEST
# ========================

if __name__ == "__main__":
    print(translate("grodów"))  # powinno dać: gord
