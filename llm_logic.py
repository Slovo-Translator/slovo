import json
import os
import re

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_json(data, filename):
    # Sortowanie osnova.json dla porządku w Arkuszach Google
    if filename == 'osnova.json':
        data = sorted(data, key=lambda x: x.get('polish', '').lower())
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def extract_grammar_info(type_and_case):
    """
    Analizuje Twoje opisy w stylu: 
    'noun - jimenьnik: "obětьnica" | accusative - vinьnik | singular | type feminine'
    """
    parts = [p.strip().lower() for p in type_and_case.split('|')]
    info = {
        "pos": "noun" if "noun" in parts[0] else "adj" if "adjective" in parts[0] else "other",
        "case": "nom",
        "num": "sg",
        "gender": "masc"
    }
    
    # Mapowanie przypadków
    case_map = {
        "nominative": "nom", "accusative": "acc", "genitive": "gen",
        "locative": "loc", "dative": "dat", "instrumental": "ins"
    }
    for k, v in case_map.items():
        if any(k in p for p in parts):
            info["case"] = v
            
    if any("plural" in p for p in parts): info["num"] = "pl"
    if any("feminine" in p for p in parts): info["gender"] = "fem"
    elif any("neuter" in p for p in parts): info["gender"] = "neut"
    
    return info

def get_vuzor_pattern(word_type_info):
    """
    Przeszukuje vuzor.json w poszukiwaniu końcówek dla danego typu gramatycznego.
    """
    vuzor_data = load_json('vuzor.json')
    patterns = {}
    
    for entry in vuzor_data:
        info = extract_grammar_info(entry.get('type and case', ''))
        # Szukamy słów o tym samym typie co nasze docelowe
        if info['pos'] == word_type_info['pos'] and info['gender'] == word_type_info['gender']:
            # Wyciągamy końcówkę (uproszczone: ostatnie 1-2 litery)
            s_word = entry.get('slovian', '')
            if s_word:
                key = f"{info['num']}_{info['case']}"
                # Tutaj silnik uczy się wzorca z pliku vuzor.json
                patterns[key] = s_word[-1] if s_word[-1] in ['a', 'o', 'e', 'y', 'ǫ', 'ъ', 'ь'] else s_word[-2:]
    return patterns

def learn_from_examples():
    """
    Główny silnik: bierze example_sentences.json i aktualizuje osnova.json.
    """
    examples = load_json('example_sentences.json')
    osnova = load_json('osnova.json')
    
    existing_polish = {item.get('polish', '').lower(): item for item in osnova}
    
    for ex in examples:
        p_word = ex.get('polish', '').lower().strip()
        s_word = ex.get('slovian', '').strip()
        
        if p_word and s_word and p_word not in existing_polish:
            # Automatyczne odcięcie końcówki bazy
            stem = s_word[:-1] if s_word[-1] in ['ъ', 'a', 'o', 'e', 'ь'] else s_word
            
            new_entry = {
                "polish": p_word,
                "slovian": s_word,
                "stem": stem,
                "type": "noun_masc" if "ъ" in s_word[-1:] else "noun_fem",
                "context": ex.get("context", "")
            }
            osnova.append(new_entry)
            print(f"Silnik: Nauczyłem się słowa '{p_word}' (rdzeń: {stem})")
            
    save_json(osnova, 'osnova.json')

def translate_sentence(sentence):
    """
    Próbuje odmienić słowa, których brakuje, korzystając ze wzorców.
    """
    osnova = load_json('osnova.json')
    words = sentence.split()
    translated = []
    
    for w in words:
        # Szukamy bazy słowa
        match = next((i for i in osnova if i['polish'] == w.lower()), None)
        if match and 'stem' in match:
            # Tutaj można dodać logikę wyboru przypadku na podstawie sąsiednich słów
            translated.append(match['slovian'])
        else:
            translated.append(w) # Fallback do oryginału
            
    return " ".join(translated)

if __name__ == "__main__":
    learn_from_examples()
