import json
import os
from collections import defaultdict

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def detect_case(tag):
    t = tag.lower()
    if "nominative" in t or "jimenovьnik" in t: return "nom"
    if "genitive" in t or "rodilьnik" in t: return "gen"
    if "accusative" in t or "vinьnik" in t: return "acc"
    if "locative" in t or "městьnik" in t: return "loc"
    if "dative" in t or "měrьnik" in t: return "dat"
    if "instrumental" in t or "orǫdьnik" in t: return "ins"
    return "nom"

def detect_number(tag):
    return "pl" if "plural" in tag.lower() or "munoga" in tag.lower() else "sg"

def build_models():
    data = load_data("vuzor.json")
    models = {}
    for e in data:
        slov = e.get("slovian", "").strip()
        tag = e.get("type and case", "")
        if not slov: continue
        lemma = tag.split('"')[1].strip() if '"' in tag else slov.split()[0]
        case = detect_case(tag)
        num = detect_number(tag)
        key = f"{num}_{case}"
        if lemma not in models:
            models[lemma] = {"endings": {}}
        models[lemma]["endings"][key] = slov
    return models

# Przyimki
PREP_RULES = {
    "w":  ("loc", "v"),
    "do": ("gen", "do"),
    "na": ("loc", "na"),
    "o":  ("loc", "o"),
    "k":  ("dat", "k"),
    "u":  ("gen", "u"),
}

# Zaimki osobowe + dzierżawcze
PRONOUNS = {
    # Osobowe
    "ja":     {"nom": "ja", "gen": "mne", "dat": "mne", "acc": "mne", "ins": "mnoju", "loc": "mne"},
    "ty":     {"nom": "ty", "gen": "tebe", "dat": "tebe", "acc": "tebe", "ins": "toboju", "loc": "tebe"},
    "on":     {"nom": "on", "gen": "jego", "dat": "jemu", "acc": "jego", "ins": "imь", "loc": "nemь"},
    "ona":    {"nom": "ona", "gen": "jeje", "dat": "jej", "acc": "jeje", "ins": "eju", "loc": "nej"},
    "my":     {"nom": "my", "gen": "nas", "dat": "nam", "acc": "nas", "ins": "nami", "loc": "nas"},
    "wy":     {"nom": "vy", "gen": "vas", "dat": "vam", "acc": "vas", "ins": "vami", "loc": "vas"},

    # Dzierżawcze
    "mój":    {"nom": "moj", "gen": "mojego", "dat": "mojemu", "acc": "mojego", "ins": "mojimь", "loc": "mojemь"},
    "moja":   {"nom": "moja", "gen": "mojeji", "dat": "mojeji", "acc": "mojǫ", "ins": "mojejǫ", "loc": "mojeji"},
    "moje":   {"nom": "moje", "gen": "mojego", "dat": "mojemu", "acc": "moje", "ins": "mojimь", "loc": "mojemь"},

    "twój":   {"nom": "tvoj", "gen": "tvojego", "dat": "tvojemu", "acc": "tvojego", "ins": "tvojimь", "loc": "tvojemь"},
    "twoja":  {"nom": "twoja", "gen": "tvojeji", "dat": "tvojeji", "acc": "tvojǫ", "ins": "tvojejǫ", "loc": "tvojeji"},
    "twoje":  {"nom": "twoje", "gen": "tvojego", "dat": "tvojemu", "acc": "twoje", "ins": "tvojimь", "loc": "tvojemь"},

    "nasz":   {"nom": "naš", "gen": "našego", "dat": "našemu", "acc": "našego", "ins": "našimь", "loc": "našemь"},
    "nasza":  {"nom": "naša", "gen": "našeji", "dat": "našeji", "acc": "našǫ", "ins": "našejǫ", "loc": "našeji"},
    "nasze":  {"nom": "naše", "gen": "našego", "dat": "našemu", "acc": "naše", "ins": "našimь", "loc": "našemь"},

    "wasz":   {"nom": "vaš", "gen": "vašego", "dat": "vašemu", "acc": "vašego", "ins": "vašimь", "loc": "vašemь"},
    "wasza":  {"nom": "vaša", "gen": "vašeji", "dat": "vašeji", "acc": "vašǫ", "ins": "vašejǫ", "loc": "vašeji"},
    "wasze":  {"nom": "vaše", "gen": "vašego", "dat": "vašemu", "acc": "vaše", "ins": "vašimь", "loc": "vašemь"},
}

def get_case_and_prep(tokens, i):
    if i == 0:
        return "nom", None
    prev = tokens[i-1].lower()
    current = tokens[i].lower()

    if prev in ("z", "ze"):
        if current.endswith(("em", "ą", "im", "ami", "mi")):
            return "ins", "su"
        return "gen", "jiz"

    if prev in PREP_RULES:
        return PREP_RULES[prev]

    return "acc", None

def decline(word, case, number, models):
    if not word:
        return "●"

    w = word.lower()

    # Zaimki (osobowe + dzierżawcze)
    if w in PRONOUNS:
        form = PRONOUNS[w].get(case, word)
        return form if form else "●"

    # Rzeczowniki / przymiotniki z vuzor.json
    best_model = None
    best_score = float("inf")
    for lemma, m in models.items():
        score = sum(a != b for a, b in zip(w, lemma.lower())) + abs(len(w) - len(lemma)) * 2
        if score < best_score:
            best_score = score
            best_model = m

    if not best_model:
        return "●"

    key = f"{number}_{case}"
    result = best_model["endings"].get(key)
    return result if result else "●"

def process(sentence):
    models = build_models()
    tokens = sentence.lower().split()
    result = []
    i = 0
    while i < len(tokens):
        word = tokens[i]
        if word in ("z", "ze"):
            i += 1
            continue
        if word in PREP_RULES:
            result.append(PREP_RULES[word][1])
            i += 1
            continue
            
        case, _ = get_case_and_prep(tokens, i)
        number = "pl" if word.endswith(("y","i","ów","ami","ach")) else "sg"
        
        translated = decline(word, case, number, models)
        result.append(translated)
        i += 1
    return " ".join(result)

# Testy
if __name__ == "__main__":
    print(process("To jest mój dom"))
    print(process("Z moim ogrodem"))
    print(process("Twoja siostra"))
    print(process("Nasze miasto"))
    print(process("Z twoją książką"))
    print(process("W naszym ogrodzie"))
